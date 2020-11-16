### 使用流程介绍
 **注意:**  以下说明中包含{*}的内容均代表变量
1. manifest.xml 文件配置
2. repo 引导命令下载
3. repo init 初始化
4. repo sync 仓库同步
5. repo start {BRANCH} [project1, project2]进行批量分支切换开始开发......
6. repo stage/repo forall -c git add . 或是 自行提交
7. repo config repo.token {ACCESS_TOKEN} 配置gitee个人API token
8. repo config repo.pullrequest {True/Fales} 配置是否开启push后，向指定分支进行的PR提交的特性
9. repo push -p --br={BRANCH} --d={DEST_BRANCH} --new_branch 用本地的指定分支向远程推送并关联，推送成功后向指定的分支进批量提交
10. repo sync 或 repo forall -c git pull 进行代码批量同步
    

### Manifest 配置例子
在名为**manifest**的仓库中创建一个default.xml文件作为repo初始化的依据  
以下为repo init初始化命令, 需要用 **-u**参数  来指定manifest的git仓库
```shell
repo init -u git@gitee.com:{namespace}/manifest.git
```
**default.xml文件用例**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote  name="gitee"
           fetch="git@gitee.com:{namespace}"     
           autodotgit="true" /> <!--fetch=".." 代表使用 repo init -u 指定的相对路径 也可用完整路径，example:https://gitee.com/MarineJ/manifest_example/blob/master/default.xml-->
  <default revision="master"
           remote="gitee" /><!--revision为默认的拉取分支，后续提pr也以revision为默认目标分支-->

  <project path="repo_test1" name="repo_test1" />  <!--git@gitee.com:{namespace}/{name}.git  name项与clone的url相关-->
  <project path="repo_test2" name="repo_test2" /> 

</manifest>
```
1、需要注意的是default 的 **revision** 属性代表着之后提交PR的目标分支    
2、不同的项目也可以有不同的 **revision** ，也就是说之后提交PR的目标分支也可不同， **revision** 的优先级由低到高  
3、fetch当前只支持gitee的ssh  

### 1. Repo 引导命令安装
```shell
# python3版本 向下兼容
curl https://gitee.com/oschina/repo/raw/fork_flow/repo-py3 > /usr/local/bin/repo
# 赋予脚本可执行权限
chmod a+x /usr/local/bin/repo
# 安装requests依赖，或在执行命令时依据提示自动安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests

# 如果安装成功但是还是提示错误，建议使用 PyEnv 进行 Python 环境的管理
https://gitee.com/mirrors/pyenv
```


### 2. Repo 初始化与仓库初次同步
```shell
mkdir your_project && cd your_project
repo init -u git@gitee.com:{namespace}/manifest.git
repo sync
```

### 3. Repo + Gitee 本地开发流程
```shell
repo start {branch} --all #  切换开发分支，当对部分仓库进行指定时，会触发仓库的预先fork

分支开发.........

repo forall -c git add ./git add/repo stage  #  批量加入暂存区或者单独加入
repo forall -c git commit/git commit  #  批量进行提交或者单独提交

repo config --global repo.token {TOKEN} #  进行gitee access_token配置, access_token获取连接 https://gitee.com/profile/personal_access_tokens
  
repo config repo.pullrequest {True/False} #  对是否触发PR进行配置 
repo push --br={BRANCH} --d={DEST_BRANCH}  #  进行推送并生成PR和审查，执行后会展示出可进行推送的项目，去掉注释的分支会进行后续推送

repo gitee-pr --br={BRANCH} #  获取项目推送后的指定分支的PR列表  
 
```
 **repo push**  参数介绍    
![输入图片说明](https://images.gitee.com/uploads/images/2020/0904/191114_41c2e24f_1332572.png "屏幕截图.png")    
1、其中值得注意的是 **--dest_branch** 和 **--br** 参数，如果不填写对应的分支的话会基于默认分支进行操作， **--br** 默认会以当前分支进行提交， **--dest_branch** 会以manifest.xml中的default  **revision** 作为默认目标分支  
2、当repo push对仓库进行推送时，会默认向与token相关的用户个人namespace下的仓库推送，在切换分支时没有预先fork成功，则在repo push失败时会再次以token关联的用户对上游仓库进行fork，fork成功后再次push即可  
3、repo push默认会以ssh方式向token关联的用户的namespace下进行仓库推送，若需要改为https，则可根据repo config repo.pushurl {用户域名空间地址如:https://gitee.com/xxxx}


 **repo**  结果详情  
![输入图片说明](https://images.gitee.com/uploads/images/2020/0727/153908_dcd3f625_1332572.png "屏幕截图.png")


 **repo gitee-pr** 参数介绍  
![输入图片说明](https://images.gitee.com/uploads/images/2020/0906/230859_93627600_1332572.png "屏幕截图.png")  
1、在 --br={BRANCH} 参数情况下直接返回指定分支下，在gitee平台上已经提交过的PR   
