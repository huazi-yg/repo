# -*- coding:utf-8 -*-
#
# Copyright (C) 2008 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import unicode_literals
from __future__ import print_function
import os
import sys

from command import Command
from git_config import IsImmutable
from git_command import git
import gitc_utils
from progress import Progress
from project import SyncBuffer
from git_config import GitConfig
from error import ForkProjectError


class Start(Command):
  common = True
  helpSummary = "Start a new branch for development"
  helpUsage = """
%prog <newbranchname> [--all | <project>...]
"""
  helpDescription = """
'%prog' begins a new branch of development, starting from the
revision specified in the manifest.
"""

  def _Options(self, p):
    p.add_option('--all',
                 dest='all', action='store_true',
                 help='begin branch in all projects')
    p.add_option('-r', '--rev', '--revision', dest='revision',
                 help='point branch at this revision instead of upstream')
    p.add_option('--head', dest='revision', action='store_const', const='HEAD',
                 help='abbreviation for --rev HEAD')

  def ValidateOptions(self, opt, args):
    if not args:
      self.Usage()

    nb = args[0]
    if not git.check_ref_format('heads/%s' % nb):
      self.OptionParser.error("'%s' is not a valid name" % nb)


  def Execute(self, opt, args):
    nb = args[0]
    err = []
    projects = []
    if not opt.all:
      projects = args[1:]
      if len(projects) < 1:
        projects = ['.']  # start it in the local project by default

    all_projects = self.GetProjects(projects,
                                    missing_ok=bool(self.gitc_manifest))


    # This must happen after we find all_projects, since GetProjects may need
    # the local directory, which will disappear once we save the GITC manifest.
    if self.gitc_manifest:
      gitc_projects = self.GetProjects(projects, manifest=self.gitc_manifest,
                                       missing_ok=True)
      for project in gitc_projects:
        if project.old_revision:
          project.already_synced = True
        else:
          project.already_synced = False
          project.old_revision = project.revisionExpr
        project.revisionExpr = None
      # Save the GITC manifest.
      gitc_utils.save_manifest(self.gitc_manifest)

      # Make sure we have a valid CWD
      if not os.path.exists(os.getcwd()):
        os.chdir(self.manifest.topdir)

    pm = Progress('Starting %s' % nb, len(all_projects))

    if not opt.all:
      fork_success_count = 0
      token = self.manifest.manifestProject.config.GetString('repo.token')
      if not token:
        token = GitConfig.ForUser().GetString('repo.token')
        if not token:
          sys.stderr.write('repo.token is None, Please set it, you need `repo config -h`\n')
          sys.exit(1)
      pushurl = self.manifest.manifestProject.config.GetString('repo.pushurl')
      success_msg = None
      for project in all_projects:
        try:
          status_code, msg = project.ForkProject(token)
          if status_code == 201:
            fork_success_count += 1
            if not success_msg:
              success_msg = msg
        except ForkProjectError:
          continue
      if fork_success_count > 0 and pushurl is None:
        ssh_url = success_msg['ssh_url']
        pushurl = ssh_url.split('/')[0]
        self.manifest.manifestProject.config.SetString('repo.pushurl',  pushurl)

    for project in all_projects:
      pm.update()

      if self.gitc_manifest:
        gitc_project = self.gitc_manifest.paths[project.relpath]
        # Sync projects that have not been opened.
        if not gitc_project.already_synced:
          proj_localdir = os.path.join(self.gitc_manifest.gitc_client_dir,
                                       project.relpath)
          project.worktree = proj_localdir
          if not os.path.exists(proj_localdir):
            os.makedirs(proj_localdir)
          project.Sync_NetworkHalf()
          sync_buf = SyncBuffer(self.manifest.manifestProject.config)
          project.Sync_LocalHalf(sync_buf)
          project.revisionId = gitc_project.old_revision

      # If the current revision is immutable, such as a SHA1, a tag or
      # a change, then we can't push back to it. Substitute with
      # dest_branch, if defined; or with manifest default revision instead.
      branch_merge = ''
      if IsImmutable(project.revisionExpr):
        if project.dest_branch:
          branch_merge = project.dest_branch
        else:
          branch_merge = self.manifest.default.revisionExpr

      if not project.StartBranch(
              nb, branch_merge=branch_merge, revision=opt.revision):
        err.append(project)
    pm.end()

    if err:
      for p in err:
        print("error: %s/: cannot start %s" % (p.relpath, nb),
              file=sys.stderr)
      sys.exit(1)
