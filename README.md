# android12_pxiel4xl

# macOS Monterey(12.21)Pixel 4xl 编译android12.0.0_r28


## 1.代号，标记 build号
>https://source.android.google.cn/setup/start/build-numbers

	SQ1A.220205.002   —>android-12.0.0_r28


## 2.刷写设备 选择设备 build
>https://source.android.com/setup/build/running#selecting-device-build
	
	Pixel 4 XL	coral	aosp_coral-userdebug

## 3.drivers
>https://developers.google.com/android/drivers

## 4.mac sdk 支持列表
>https://www.jianshu.com/p/37f5f826b642

### 如何创建可引导的 macOS 安装器
https://support.apple.com/zh-cn/HT201372
### macOS monterey 兼容Xcode 12
>https://stackoverflow.com/questions/69994916/how-can-i-run-xcode-12-5-1-on-monterey

## 5.mac 编译android 坑,Mac Mojave编译AOSP趟坑
>https://blog.csdn.net/weixin_39895167/article/details/117529470

## 6.xcode 各版本下载
>https://developer.apple.com/download/all/?q=xcode


## 7.mac 环境变量设置
### bash_profile
export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo'  
JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.8.0_321.jdk/Contents  
PATH=$JAVA_HOME/bin:$PATH:.  
CLASSPATH=$JAVA_HOME/lib/tools.jar:$JAVA_HOME/lib/dt.jar:.  
export JAVA_HOME  
export PATH  
export CLASSPATH  

### android_env
export ANDROID_HOME=/Users/mac/Library/android/sdk  
export PATH=${PATH}:${ANDROID_HOME}/tools  
export PATH=${PATH}:${ANDROID_HOME}/platform-tools  

### zshrc
ZSH_THEME="gentoo"   
source .bash_profile'''  

### 8.初始化仓库(使用清华的代码源)
mkdir ~/bin  
PATH=~/bin:$PATH  
curl https://mirrors.tuna.tsinghua.edu.cn/git/git-repo > ~/bin/repo  
chmod a+x ~/bin/repo  

打开bin文件夹下的repo文件，将REPO_URL = 'https://gerrit.googlesource.com/git-repo'  
改为 REPO_URL = 'https://mirrors.tuna.tsinghua.edu.cn/git/git-repo‘  

repo init -u https://mirrors.tuna.tsinghua.edu.cn/git/AOSP/platform/manifest -b android-11.0.0_r41 --depth=1  
repo sync -f -j3  

## 9.编译，清理
make clobber  
source build/envsetup.sh  
lunch  
make -j8  

vim build/soong/cc/config/x86_darwin_host.go  

android-11.0.0_r1

	       "10.10",
		"10.11",
		"10.12",
		"10.13",
		"10.14",
		"10.15",

## 10.开始刷机
source build/envsetup.sh  
lunch  

adb reboot bootloader  
cd /out   
fastboot -w flashall  

fastboot: error: ANDROID_PRODUCT_OUT not set错误  
source build/envsetup.sh  
lunch  

## 11.AndroidStudio中查看源码

使用Android Studio导入AOSP源码的奇技淫巧

>https://www.jianshu.com/p/2ba5d6bd461e

>https://blog.csdn.net/chenkai19920410/article/details/53263352

mmm development/tools/idegen/

注：如果刚才编译AOSP的那个命令行窗口关闭了，必须要在执行source build/envsetup.sh一次，用了初始化编译环境

sudo ./development/tools/idegen/idegen.sh

>https://www.jianshu.com/p/f2066b9e404b

>https://studygolang.com/articles/32127

mm编译当前目录下的模块，不编译依赖模块  
mmm：编译指定目录下的模块，不编译它所依赖的其它模块。  
mma：编译当前目录下的模块及其依赖项。     
mmma：编译指定路径下所有模块，并且包含依赖。   

>如果你修改了源码，想查看生成的APK文件，有两种方式：  
1. 通过adb push或者adb install 来安装APK。  
2. 使用make snod命令，重新生成 system.img，运行模拟器查看  


## 12.修改编译Frameworks的代码
在根目标执行  
make framework 或者 cd  rameworks/base/core/java/android
mmm ./app  
make framework  make systemimage  

mmm ./xx/xx/app  
make snod

### 刷机 

## 13.Magisk	 and Xposed

>http://www.juneleo.cn/47a3736f9762/

## 14.android 系统需求开发的分析步骤

查看所有进程 adb shell    ps -A  
查看某应用的进程 ps -A |grep “com.mic.app”   ps -A | grep "setting"  
查看某进程的log    logcat |grep “pid”  


