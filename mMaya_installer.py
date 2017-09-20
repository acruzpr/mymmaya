# Please refer to the license information found in the mMaya folder, ../mMaya/LICENSE/Molecular_Maya_license.txt


import urllib, urllib2, traceback, os, sys, shutil, zipfile, StringIO, ftplib, uuid, cStringIO, time

import __main__

import maya.cmds as cmds, maya.mel as mel

version = 'v2.1.1'

pyVer_2711Plus = sys.version_info > (2, 7, 11)

class MMaya_installer(object):
    
    def __init__(self):
        
        if False:
            cmds.confirmDialog(
                title = 'server issue',
                message = ('We are currently [~13th April 2016] experiencing some known server related issues, please check back and try again in a day or two. Our apologies for any inconveniences.'),
                button = 'ok'
            )
            return
        
        self.kCancelInstall = 'cancel installation'
        
        mayaYrVern = int(cmds.about(v = True)[:4])
        self.isMaya2018Plus = (mayaYrVern >= 2018)
        self.isMaya2017Plus = (mayaYrVern >= 2017)
        self.isMaya2016Plus = (mayaYrVern >= 2016)
        self.isMaya2015Plus = (mayaYrVern >= 2015)
        self.isMaya2014Plus = (mayaYrVern >= 2014)
        
        self.installProgress = None
        
        self.clarafiPassEntered = ''
        self.clarafiPassStarEdit = False
        
        self.installerUser = None
        self.supportedOSs = ('win64', 'mac', 'linux64')
        
        self.build_installerGUI()
        
        print 'mMaya installer ver:', version
    
    def __del__(self):
        pass
    
    def isSupportedPlatform(self):
        
        if self.isMaya2018Plus:
            resp = cmds.confirmDialog(
                title = 'Maya 2018 not supported',
                message = 'Molecular Maya is not currently supported under Maya 2018. We hope to have an update soon.\n\nThanks for bearing with us.\n',
                button = ('ok',)
            )
            return False
        
        return True
    
    
    def AssDep(self):
        
        
        
        ArnoldPlug = 'mtoa'
        if not cmds.pluginInfo(ArnoldPlug, l = 1, q = 1):
            try:
                cmds.loadPlugin(ArnoldPlug, qt = True)
            except:
                
                
                
                userSetup_filePath = mel.eval('whatIs userSetup')
                if userSetup_filePath == 'Unknown':
                    userSetup_filePath = None
                else:
                    userSetup_filePath = userSetup_filePath.replace('Script found in: ', '')
                
                genericMRMsg = ('Please install it, and try again. Molecular Maya boot aborted.\n\nFeel free to contact us if you need further help.\n\n[ To remove this message altogether, and mMaya attempting to boot, edit/comment out the mMaya related line in your userSetup.mel' +('.' if not userSetup_filePath else ', which is located here: ' +userSetup_filePath)+ ' ]')
                genericMRMsg_start = '\nMolecular Maya for Maya 2017+ requires that the Arnold renderer be installed, which it appears not to be.'
                
                cmds.confirmDialog(
                    title = 'Molecular Maya, Arnold requirement',
                    message = (genericMRMsg_start+ '\n\nIt may not have been selected during your main Maya installation process. It is included as part of the default Maya 2017 install package.' +genericMRMsg),
                    button = 'ok'
                )
                
                return False
        
        return True
    
    
    def MRDep(self):
        
        MRPlug = 'Mayatomr'
        if not cmds.pluginInfo(MRPlug, l = 1, q = 1):
            try:
                cmds.loadPlugin(MRPlug, qt = True)
            except:
                
                
                
                userSetup_filePath = mel.eval('whatIs userSetup')
                if userSetup_filePath == 'Unknown':
                    userSetup_filePath = None
                else:
                    userSetup_filePath = userSetup_filePath.replace('Script found in: ', '')
                
                genericMRMsg = ('Please install it, and try again. Molecular Maya installation canceled.\n\nFeel free to contact us if you need further help.\n\n[ To remove this message altogether, and mMaya attempting to boot, edit/comment out the mMaya related line in your userSetup.mel' +('.' if not userSetup_filePath else ', which is located here: ' +userSetup_filePath)+ ' ]')
                genericMRMsg_start = '\nMolecular Maya requires that the Mental Ray renderer be installed, which it appears not to be.'
                if self.isMaya2016Plus:
                    
                    launchPage = 'launch Autodesk download page'
                    resp = cmds.confirmDialog(
                        title = 'Molecular Maya, Mental Ray requirement',
                        
                        message = (genericMRMsg_start+ '\n\nFor Maya 2016+, you need to download it separately and install it. Search google or the Autodesk page for your exact Maya version (extensions, service packs...), and possibly in your online Autodek Account Management console (for base versions), to be able to find the exact corresponding mental ray installation package for that version. You may need uninstall previous mental ray versions, in order to install new correctly. Etc. Or use Autodesk\'s LiveUpdate manager.' +genericMRMsg),
                        button = ('ok')
                    )
                    if resp == launchPage:
                        
                        cmds.evalDeferred(lambda: cmds.showHelp('http://knowledge.autodesk.com/support/maya/downloads/caas/downloads/content/mental-ray-plugin-for-maya-2016.html', absolute = True))
                
                else:
                    
                    cmds.confirmDialog(
                        title = 'Molecular Maya, Mental Ray requirement',
                        message = (genericMRMsg_start+ '\n\nIt may not have been selected during your main Maya installation process. ' +genericMRMsg),
                        button = 'ok'
                    )
                
                return False
        
        return True
    
    
    def cancelInstall(self):
        
        
        print ('mMaya installation canceled, cleaning up. [' +str(self.installProgress)+ ']')
        
        
        
        infoTxts = [self.initInstallPrompt_txt, self.installationPath_txt, self.downloadInProgress_txt, self.packageExplosionInProgress_txt, self.usersetupEditPrompt_txt, self.installComplete_txt]
        for infoTxt in infoTxts:
            cmds.text(infoTxt, e = True, label = '')
        cmds.text(self.downloadInProgress_txt, e = True,
            
            enable = True,
            label = '> Canceled. Cleaning up...',
        )
        cmds.refresh()
        
        self.removeWrittenFilesAndFolders()
        
        if self.installProgress == None:
            cmds.deleteUI(self.win)
        
        cmds.file(new = True, f = True)
    
    
    def installationPathAngling(self, startPath):
        
        selFolder = cmds.fileDialog2(
            caption = 'select folder to install mMaya in to',
            okCaption = 'Select',
            startingDirectory = startPath,
            dialogStyle = 2,
            fileMode = 3,
        )
        
        return selFolder
    
    
    def testInstallPathWritability(self):
        
        
        
        writeTestPath = (self.installPath + '/writeTest')
        if os.path.isdir(writeTestPath):
            cmds.warning('>> ? - writeTestPath already exists...')
            return False
        
        try:
            os.makedirs(writeTestPath)
        except:
            cmds.warning('>> ! unable to create dir in mMaya install path')
            return False
        else:
            
            
            
            allStillHappy = True
            
            writeTestPath_file = (writeTestPath+ '/writeFileTest')
            try:
                
                fh = open(writeTestPath_file, 'w')
                fh.close()
                
            except:
                
                cmds.warning('>> ! unable to write a file within created folder of mMaya install path')
                allStillHappy = False
                
            else:
                
                try:
                    os.remove(writeTestPath_file)
                except:
                    cmds.warning(('>> ? - unable to remove the writeTestPath_file (' +writeTestPath_file+ ') we created just a moment ago...'))
                    allStillHappy = False
            
            
            
            
            try:
                os.removedirs(writeTestPath)
            except:
                cmds.warning(('>> ? - unable to remove the writeTestPath (' +writeTestPath+ ') we created just a moment ago...'))
                allStillHappy = False
            
            if not allStillHappy:
                return False
        
        return True
    
    
    def removeWrittenFilesAndFolders(self):
        
        
        try:
            self.writtenFilePaths
            self.writtenFolderPaths
        except AttributeError:
            pass
        else:
            
            for writtenFilePath in self.writtenFilePaths:
                try:
                    os.remove(writtenFilePath)
                except:
                    print ('!>> was unable to remove written file: ' +writtenFilePath)
            
            
            
            
            
            remDirs_stopNubFilePath = (self.installPath+ '/remDirs_stopNub')
            try:
                open(remDirs_stopNubFilePath, 'w')
            except:
                pass
            
            for writtenFolderPath in self.writtenFolderPaths:
                
                
                try:
                    os.removedirs(writtenFolderPath)
                except:
                    pass
                    
                
                
            
            try:
                os.remove(remDirs_stopNubFilePath)
            except:
                pass
    
    
    def initInstall_installationPath(self):
        
        
        
        
        
        
        
        self.installProgress = 'initInstall_installationPath'
        
        try:
            
            self.cmdRepWin()
            
            if not self.isSupportedPlatform():
                self.installProgress = 'unsupported platform'
                self.cancelInstall()
                return
            
            if self.isMaya2017Plus:
                if not self.AssDep():
                    self.installProgress = 'Arnold dep not present'
                    self.cancelInstall()
                    return
            else:
                if not self.MRDep():
                    self.installProgress = 'MR dep not present'
                    self.cancelInstall()
                    return
            
            resp = cmds.layoutDialog(
                ui = self.build_clarafiLoginWin
            )
            if resp != 'happyCampers':
                '''
                    Dear "malicious intent" script reader,
                        Yeah, go on, take money/info/time from a small, independent organisation that does what it does to help humans do the good stuff that they do, better.
                        For those that dont have such intent... yeah, this is about as soft as it gets w/o spending time on a next click up compiled/hidden method.
                '''
                if resp == 'unhappyCamper':
                    self.installProgress = 'unhappy clarafi login'
                elif resp == 'clarafiLoginAbort' or resp == 'dismiss':
                    self.installProgress = 'clarafiLoginAbort'
                self.cancelInstall()
                return
            
            cmds.layout(self.initInstallBtns_fmL, e = True, enable = False)
            
            cmds.control(self.initInstallPrompt_txt, e = True, enable = False)
            cmds.text(self.installationPath_txt, e = True,
                enable = True,
                label = '> installation path'
            )
            
            useRecommendedPath = 'use recommended'
            chooseOwnPath = 'choose path'
            chooseAgain = 'choose again'
            
            recommendedPath = (cmds.internalVar(uad = True)[:-1]+ '/scripts')
            
            resp = cmds.confirmDialog(
                title = 'installation path selection',
                message = ('Choose a path to install mMaya in to. You may choose the recommended, or your own.\nInstallation into a path containing an older mMaya version is fine.\n\nRecommended path: ' +recommendedPath+ '\n'),
                button = (useRecommendedPath, chooseOwnPath, self.kCancelInstall)
            )
            if resp == self.kCancelInstall:
                
                self.cancelInstall()
                return
                
            elif resp == useRecommendedPath:
                
                installPath = recommendedPath
                
            elif resp == chooseOwnPath:
                
                selPath = self.installationPathAngling(recommendedPath)
                while not selPath:
                    resp = cmds.confirmDialog(
                        title = 'no path choosen',
                        message = ('Choose a path to install mMaya in to. You may choose the recommended, or your own.\nInstallation into a path containing an older mMaya version is fine.\n\nRecommended path: ' +recommendedPath+ '\n'),
                        button = (useRecommendedPath, chooseAgain, self.kCancelInstall)
                    )
                    if resp == self.kCancelInstall:
                        self.cancelInstall()
                        return
                    elif resp == useRecommendedPath:
                        
                        selPath = [recommendedPath]
                        break
                    elif resp == chooseAgain:
                        selPath = self.installationPathAngling(recommendedPath)
                
                installPath = selPath[0]
            
            print 'mMaya installation path:', installPath
            self.installPath = installPath
            
            
            
            if not self.testInstallPathWritability():
                
                resp = cmds.confirmDialog(
                    title = 'unable to write to installation path',
                    message = ('The choosen path to install mMaya into is unable to be written to. Check permissions, or try another path.\n\n' +installPath+ '\n'),
                    button = (chooseAgain, self.kCancelInstall)
                )
                if resp == chooseAgain:
                    self.initInstall_installationPath()
                elif resp == self.kCancelInstall:
                    self.cancelInstall()
                return
                
            else:
                
                
                self.download_mMaya_installPackage()
            
        except Exception as e:
            
            self.installProgress = (self.installProgress+ ' !! installation exception')
            
            print 'unhandled installation exception:'
            print ('='*20+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
            
        finally:
            
            
            if self.installProgress != 'completeInstall, complete.':
                
                
                
                try:
                    
                    cmds.waitCursor(state = True)
                    
                    if False:
                        feedbacker_content = open((__main__.mMaya_root_obj.mMaya_root_path+ '/mMaya_feedbacker_versions/mMaya_feedbacker_v0.0.0/mMaya_feedbacker.py')).read()
                    else:
                        feedbacker_content = urllib.urlopen('https://s3-us-west-1.amazonaws.com/mmaya/mMaya_feedbacker.py').read()
                    
                except:
                    
                    
                    
                    
                    pass
                    
                else:
                    
                    try:
                        
                        
                        exec(feedbacker_content) in globals()
                        
                    except Exception as e:
                        
                        
                        
                        print 'exec issue: exec(feedbacker_content) in globals()'
                        pass
                        
                    else:
                        
                        try:
                            
                            mMaya_feedbacker_obj = MMaya_feedbacker(installFeedack = True)
                            if self.installerUser:
                                cmds.textFieldGrp(mMaya_feedbacker_obj.replyToName_txtFldGrp, e = True, text = self.installerUser)
                                cmds.textFieldGrp(mMaya_feedbacker_obj.replyToEmailAdd_txtFldGrp, e = True, text = 'mMaya_installer@clarafi.com')
                            else:
                                cmds.checkBoxGrp(mMaya_feedbacker_obj.anonymous_cBox, e = True, v1 = True)
                            cmds.scrollField(mMaya_feedbacker_obj.messageBody_scrlField, e = True, text = ('_mMayaInstallProgress_: ' +self.installProgress))
                            mMaya_feedbacker_obj.mailSentMsg = False
                            
                            mMaya_feedbacker_obj.post()
                            
                        except:
                            
                            pass
                
                finally:
                    
                    cmds.waitCursor(state = False)
                
                
            else:
                
                
                
                cmds.text(self.installComplete_txt, e = True,
                    label = ('> complete!'),
                    enable = True
                )
                cmds.refresh()
                
                signOffMsg = 'Please click on the mMaya banner to visit us on Clarafi.com for training, further resources, feedback and support. Also receive software updates, and newly purchased kits by using the \'updates\' button at the bottom of the mMaya Editor.\n\nHappy modeling,\nThe Clarafi Team.\n'
                
                if not self.reqReboot:
                    sys.path.append((self.installPath+ '/mMaya'))
                    try:
                        import mMaya_rootEnv
                    except ImportError:
                        self.reqReboot = True
                
                if self.reqReboot:
                    signOffButton = '[ ok ]'
                    signOffMsg += '\n[ To boot newly installed mMaya, close Maya and restart it ]\n'
                else:
                    signOffButton = '[ boot mMaya now ]'
                
                cmds.confirmDialog(
                    title = 'Installation successful.',
                    message = signOffMsg,
                    button = signOffButton
                )
                
                
                if not self.reqReboot:
                    
                    
                    
                    __main__.mMaya_rootEnv = mMaya_rootEnv
                    mMaya_rootEnv.init()
            
            
            if cmds.window(self.win, exists = True):
                cmds.deleteUI(self.win)
            
            cmds.file(new = True, f = True)
            
    
    
    def download_mMaya_installPackage(self):
        
        
        
        self.installProgress = 'download_mMaya_installPackage'
        
        cmds.waitCursor(state = True)
        
        cmds.control(self.installationPath_txt, e = True, enable = False)
        cmds.control(self.downloadInProgress_txt, e = True, enable = True)
        
        try:
            page_obj = urllib.urlopen('https://s3-us-west-1.amazonaws.com/mmaya/mMaya_installPackage.zip')
            metaData = page_obj.info()
            mMaya_installPackage_size = metaData.getheaders('Content-Length')[0]
            mMaya_installPackage_size = round(int(mMaya_installPackage_size)/1000000., 1)
            
        except Exception as e:
            print 'problem accessing mMaya_installPackage:'
            print ('='*20+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
            cmds.waitCursor(state = False)
            cmds.confirmDialog(
                title = 'connectivity problem',
                message = 'Unable to access web resource for mMaya installation. Try again later.\n\nInstallation aborted. If problem persists, feel free to contact us.\n',
                button = 'ok'
            )
            self.cancelInstall()
            return
        
        cmds.text(self.downloadInProgress_txt, e = True,
            label = ('> download install package\n   downloading... (~' +str(mMaya_installPackage_size)+ 'MB)')
        )
        cmds.refresh()
        
        try:
            
            mMaya_installPackage_content = page_obj.read()
            
        except Exception as e:
            print 'problem downloading mMaya_installPackage:'
            print ('='*20+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
            cmds.waitCursor(state = False)
            cmds.confirmDialog(
                title = 'connectivity problem',
                message = 'Unable to access web resource for mMaya installation. Try again later.\n\nInstallation aborted. If problem persists, feel free to contact us.\n',
                button = 'ok'
            )
            self.cancelInstall()
            return
        
        self.mMaya_installPackage_content = mMaya_installPackage_content
        
        
        
        
        self.explode_mMaya_installPackage()
    
    
    def explode_mMaya_installPackage(self):
        
        
        
        self.installProgress = 'explode_mMaya_installPackage'
        
        cmds.text(self.downloadInProgress_txt, e = True,
            label = ('> download install package'),
            enable = False
        )
        cmds.text(self.packageExplosionInProgress_txt, e = True,
            label = ('> install package'),
            enable = True
        )
        cmds.refresh()
        
        zipFileIntegrityIssue, packageExplosionIssue = [False]*2
        writtenFilePaths = []
        writtenFolderPaths = []
        
        try:
            
            package_zipFileObj = zipfile.ZipFile(StringIO.StringIO(self.mMaya_installPackage_content), 'r')
            
        except Exception as e:
            
            zipFileIntegrityIssue = ('opening archive mMaya_installPackage.zip')
            print ('='*20+ '\n' +zipFileIntegrityIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
            
        else:
            
            package_files = package_zipFileObj.namelist()
            for package_file in package_files:
                
                local_package_filePath = (self.installPath+ '/' +package_file)
                local_package_parentFolder = os.path.dirname(local_package_filePath)
                
                if not os.path.isdir(local_package_parentFolder):
                    try:
                        os.makedirs(local_package_parentFolder)
                        writtenFolderPaths.append(local_package_parentFolder)
                    except Exception as e:
                        packageExplosionIssue = ('creating directory ' +local_package_parentFolder)
                        print ('='*20+ '\n' +packageExplosionIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
                        break
                
                if package_file.endswith('/'):
                    continue
                
                try:
                    local_package_filePath_obj = open(local_package_filePath, 'w')
                except Exception as e:
                    packageExplosionIssue = ('opening local file ' +local_package_filePath)
                    print ('='*20+ '\n' +packageExplosionIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
                    break
                else:
                    writtenFilePaths.append(local_package_filePath)
                
                
                try:
                    package_file_content = package_zipFileObj.read(package_file)
                except Exception as e:
                    packageExplosionIssue = ('reading package file mMaya_installPackage.zip/' +package_file)
                    print ('='*20+ '\n' +packageExplosionIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
                    break
                
                try:
                    local_package_filePath_obj.write(package_file_content)
                except Exception as e:
                    packageExplosionIssue = ('writing to local file ' +local_package_filePath)
                    print ('='*20+ '\n' +packageExplosionIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
                    break
                
                try:
                    local_package_filePath_obj.close()
                except Exception as e:
                    packageExplosionIssue = ('closing local file ' +local_package_filePath)
                    print ('='*20+ '\n' +packageExplosionIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
                    break
            
            
            try:
                package_zipFileObj.close()
            except Exception as e:
                zipFileIntegrityIssue = ('closing archive mMaya_installPackage.zip')
                print ('='*20+ '\n' +zipFileIntegrityIssue+ '\n' +traceback.format_exc(e)+ '\n' +'='*20)
        
        
        self.writtenFilePaths = writtenFilePaths
        self.writtenFolderPaths = writtenFolderPaths
        
        
        
        if (zipFileIntegrityIssue or packageExplosionIssue):
            
            
            
            
            
            
            
            
            cmds.waitCursor(state = False)
            if zipFileIntegrityIssue:
                print '>> zipFileIntegrityIssue:', zipFileIntegrityIssue
                cmds.confirmDialog(
                    title = 'connectivity/archive problem?',
                    message = ('The downloaded archive appears to have a problem: ' +zipFileIntegrityIssue+ '.\nPossible download interuption, try again later.\n\nInstallation aborted. If problem persists, feel free to contact us.\n'),
                    button = 'ok'
                )
            if packageExplosionIssue:
                print '>> packageExplosionIssue:', packageExplosionIssue
                cmds.confirmDialog(
                    title = 'archive extraction issues',
                    message = ('Problems encountered during downloaded archvie extraction: ' +packageExplosionIssue+ '.\n\nAttempt to download again later, or resolve filesystem permissions if that seems apparent.\n\nInstallation aborted. If problem persists, feel free to contact us.\n'),
                    button = 'ok'
                )
            
            
            self.cancelInstall()
            return
            
        else:
            
            
            cmds.waitCursor(state = False)
            self.userSetupEntryMod()
    
    
    def userSetupEntryMod(self):
        
        
        
        
        self.installProgress = 'userSetupEntryMod'
        
        cmds.control(self.packageExplosionInProgress_txt, e = True, enable = False)
        cmds.text(self.usersetupEditPrompt_txt, e = True,
            label = ('> edit userSetup'),
            enable = True
        )
        cmds.refresh()
        
        userSetup_filePath = mel.eval('whatIs userSetup')
        if userSetup_filePath == 'Unknown':
            userSetup_exists = False
        else:
            userSetup_exists = True
            self.userSetup_filePath = userSetup_filePath.replace('Script found in: ', '')
        
        self.userSetup_initEntry = 'python("import sys; sys.path.append(\'' +self.installPath+ '/mMaya\'); import mMaya_rootEnv; mMaya_rootEnv.init()");'
        print ('\nmMaya, userSetup.mel line to append ' +(('(located here: ' +self.userSetup_filePath+ ')') if userSetup_exists else '')+ ':\n') 
        print self.userSetup_initEntry
        print ''
        
        addForMe = 'add it (default)'
        addForMe_andShow = 'add it, review changes first'
        illDoIt = 'I\'ll add it (show me details)'
        resp = cmds.confirmDialog(
            title = 'userSetup.mel addition',
            message = 'Installation of mMaya requires that a line be appended to your userSetup.mel,\n\nDo you wish to have this done automatically, or do it yourself by hand?\n',
            button = (addForMe, addForMe_andShow, illDoIt, self.kCancelInstall)
        )
        
        if resp == self.kCancelInstall:
            
            self.cancelInstall()
            return
        
        elif resp == illDoIt:
            
            if userSetup_exists:
                userSetupLocNote = ('The current userSetup.mel file can be found here:\n\n ' +self.userSetup_filePath+ '\n\n')
            else:
                userSetupLocNote = ('Note, there appears to be no userSetup.mel created yet, see Maya docs for more info.\n\n')
            
            addForMe_2 = 'actually, add it for me but show mods for my review prior to writing'
            resp = cmds.confirmDialog(
                title = 'userSetup.mel addition, details',
                message = ('In order for Molecualr Maya to boot each time Maya does, the following entry must be added to your userSetup.mel (see ../mMaya/userSetupAddition.txt [also, printed to scriptEditor for copy-paste])\n\n' +self.userSetup_initEntry+ '\n\n' +userSetupLocNote),
                button = ('ok', addForMe_2, self.kCancelInstall)
            )
            if resp == self.kCancelInstall:
                self.cancelInstall()
                return
            if resp == addForMe_2:
                resp = addForMe_andShow
            else:
                pass
        
        if resp == addForMe or resp == addForMe_andShow:
            
            if not userSetup_exists:
                
                
                
                userScriptsDir = cmds.internalVar(usd = True)
                self.userSetup_filePath = (userScriptsDir+ 'userSetup.mel')
                
                try:
                    
                    open(self.userSetup_filePath, 'w')
                    
                except:
                    print '>> unable to create new userSetup.mel'
                    cmds.confirmDialog(
                        title = 'unable to create new userSetup.mel',
                        message = ('Unable to write to scripts directory in order to create a new userSetup.mel:\n\n' +userScriptsDir+ '\n\nThis will prevent mMaya from being able to boot each Maya session. Check write permissions on the path and try again. Installation aborted.'),
                        button = 'ok'
                    )
                    self.cancelInstall()
                    return
            
            
            if resp == addForMe_andShow:
                
                resp = cmds.layoutDialog(
                    ui = self.build_userSetupMod_layoutDialog
                )
                if resp == 'commitUserSetupEdit':
                    if not self.mMayaInstall_editUserSet(test = False):
                        return
                else:
                    if resp == 'cancelInstall':
                        self.cancelInstall()
                        return
                    else:
                        
                        commit = 'commit changes'
                        resp = cmds.confirmDialog(
                            title = 'userSetup.mel mod review cancel...',
                            message = ('Did the append look ok? Commit, or abort installation?'),
                            button = (commit, self.kCancelInstall)
                        )
                        if resp == commit:
                            if not self.mMayaInstall_editUserSet(test = False):
                                return
                        else:
                            self.cancelInstall()
                            return
            else:
                
                
                if not self.mMayaInstall_editUserSet(test = False):
                    return
        
        
        
        
        
        self.completeInstall()
    
    
    def hotkeyEntry(self):
        
        
        
        
        self.installProgress = 'hotkeyEntry'
        
        cmds.control(self.usersetupEditPrompt_txt, e = True, enable = False)
        cmds.text(self.hotkeyEntryPrompt_txt, e = True,
            label = ('> hotkey'),
            enable = True
        )
        cmds.refresh()
        
        
        
        
        cmds.runTimeCommand('Toggle_mMayaEd_RTC',
            e = cmds.runTimeCommand('Toggle_mMayaEd_RTC', q = True, exists = True),
            annotation = 'Toggle mMaya Editor on/off',
            category = 'Display',
            command = 'mMaya_root_obj.mMaya_root_GUIObj.mMaya_toggleEditor()'
        )
        cmds.nameCommand('Toggle_mMayaEd_RTC_nameCommand', ann = 'Toggle_mMayaEd_RTC', c = 'Toggle_mMayaEd_RTC')
        
        hotkeyAlreadyBound = False
        nbNamedCmds = cmds.assignCommand(query = True, numElements = True)
        for idx in xrange(1, (nbNamedCmds + 1)):
            cmdAssign = cmds.assignCommand(idx, query = True, command = True)
            if cmdAssign == 'Toggle_mMayaEd_RTC':
                assignedKeyArray = cmds.assignCommand(idx, query = True, keyArray = True)
                if assignedKeyArray:
                    hotkeyAlreadyBound = assignedKeyArray
            if cmdAssign == 'ToggleMolEditor':
                assignedKeyArray = cmds.assignCommand(idx, query = True, keyArray = True)
                if assignedKeyArray:
                    cmds.hotkey(
                        k = assignedKeyArray[0],
                        alt = assignedKeyArray[1],
                        ctl = assignedKeyArray[2],
                        cmd = assignedKeyArray[4],
                        name = '',
                        releaseName = '',
                    )
        
        if hotkeyAlreadyBound:
            cmds.text(self.hotkeyEntryPrompt_txt, e = True,
                label = ('> hotkey\n   - assigned already'),
                enable = True
            )
            cmds.refresh()
            hotkeyCombo_words = []
            if assignedKeyArray[1] == '1':
                if cmds.about(mac = True):
                    hotkeyCombo_words.append('option')
                else:
                    hotkeyCombo_words.append('alt')
            if assignedKeyArray[2] == '1':
                if cmds.about(mac = True):
                    hotkeyCombo_words.append('control')
                else:
                    hotkeyCombo_words.append('ctrl')
            if assignedKeyArray[4] == '1':
                hotkeyCombo_words.append('command')
            if assignedKeyArray[0]:
                hotkeyCombo_words.append(assignedKeyArray[0])
            
            hotkeyCombo_words = ' + '.join(hotkeyCombo_words)
            
            cmds.confirmDialog(
                title = 'mMaya Editor hotkey',
                message = ('It appears you already have a hotkey assigned for toggling the mMaya Editor:\n\n' +hotkeyCombo_words+ ''),
                button = 'ok'
            )
            
        else:
            
            if cmds.about(mac = True):
                suggestedHotkeyCombo = '"a" 1 0 1 1'
                suggestedHotkeyCombo_words = 'We recommend command-control-a, due to its similarity with control-a for the Attribute Editor.'
                cmdModifier = True; altModifier = False 
            else:
                suggestedHotkeyCombo = '"a" 1 1 0 1'
                suggestedHotkeyCombo_words = 'We recommend alt-ctrl-a, due to its similarity with ctrl-a for the Attribute Editor.'
                cmdModifier = False; altModifier = True
            
            if self.isMaya2016Plus:
                whereToFindHotkey_words = 'via the "Search By" field, "Runtime Command", and entering in search term "mMaya" to see "Toggle_mMayaEd_RTC" listed. Refer to mMaya documentation if you forget.'
            else:
                whereToFindHotkey_words = 'by selecting the "Display" category and locating command "Toggle_mMayaEd_RTC" near the bottom. Refer to mMaya documentation if you forget.'
            
            mel.eval('source hotkeyEditor.mel')
            suggestedHotkeyCombo_alreadyAssigned = mel.eval('getHotkeyCommandNew ' +suggestedHotkeyCombo)
            
            if suggestedHotkeyCombo_alreadyAssigned:
                
                cmds.confirmDialog(
                    title = 'mMaya Editor hotkey',
                    message = ('You may like to assign a hotkey to show the mMaya Editor. '+suggestedHotkeyCombo_words+ ' This hotkey-combo appears to be taken already. To assign a different hotkey later, in the Hotkey Editor (Windows > Settings/prefs > Hotkey Editor) you can find the Molecule Editor toggler command to assign a hotkey to ' +whereToFindHotkey_words),
                    button = 'ok'
                )
                
            else:
                
                assignHotkey = 'yes, assign it'
                assignLater = 'no, i might assign one later'
                resp = cmds.confirmDialog(
                    title = 'mMaya Editor hotkey',
                    message = ('You may like to assign a hotkey to show the mMaya Editor. '+suggestedHotkeyCombo_words+' Would you like this to be assigned now?'),
                    button = (assignHotkey, assignLater)
                )
                if resp == assignHotkey:
                    
                    cmds.hotkey(
                        k = 'a',
                        ctl = True,
                        alt = altModifier,
                        cmd = cmdModifier,
                        name = 'Toggle_mMayaEd_RTC_nameCommand',
                        pressCommandRepeat = False
                    )
                    
                else:
                    
                    resp = cmds.confirmDialog(
                        title = 'mMaya Editor hotkey',
                        message = ('To assign a hotkey later, in the Hotkey Editor (Windows > Settings/prefs > Hotkey Editor) you can find the Editor toggler command to assign a hotkey to ' +whereToFindHotkey_words),
                        button = 'ok'
                    )
            
            
            if False:
                
                
                mel.eval('HotkeyPreferencesWindow;')
                cmds.textScrollList('HotkeyEditorCategoryTextScrollList', e = True, si = 'Display')
                mel.eval('hotkeyEditorCategoryTextScrollListSelect;')
                cmds.textScrollList('HotkeyEditorCommandTextScrollList', e = True, si = 'Toggle_mMayaEd_RTC')
                mel.eval('hotkeyEditorCommandTextScrollListSelect;')
        
        
        
        self.completeInstall()
    
    
    def completeInstall(self):
        
        self.installProgress = 'completeInstall, init'
        
        if False:
            
            
            cmds.text(self.hotkeyEntryPrompt_txt, e = True,
                label = ('> hotkey'),
                enable = False
            )
        else:
            cmds.control(self.usersetupEditPrompt_txt, e = True, enable = False)
            cmds.text(self.installComplete_txt, e = True,
                label = ('> finishing up...'),
                enable = True
            )
            cmds.refresh()
        
        if False:
            cmds.waitCursor(state = True)
            try:
                ftpObj = ftplib.FTP('52.11.112.240', 'mMaya_userFTP', 'mMaya_userFTPPass')
                ftpObj.cwd('/mMaya_installs')
                ftpObj.storbinary(('STOR ' + 'instMAC_' +str(uuid.getnode())+ '_' +str(time.time())), cStringIO.StringIO(open((self.installPath+ '/mMaya/.installPackageVer')).readline()))
                ftpObj.quit()
            except:
                pass
            cmds.waitCursor(state = False)
        
        
        reqReboot = False
        mMaya2Present = False
        try:
            __main__.mMaya
        except AttributeError:
            
            
            try:
                __main__.mMaya_rootEnv
            except AttributeError:
                
                
                try:
                    __main__.mMaya_root
                except AttributeError:
                    
                    
                    pass
                else:
                    
                    
                    reqReboot = True
            else:
                
                
                mMaya2Present = True
                reqReboot = True
        else:
            
            
            reqReboot = True
        
        '''
        if False and mMaya2Present:
            # needs some more work..., potentially deferredEval
            #
            notGoingToWork_reboot = False
            
            curInstallPath = __main__.mMaya_root_obj.mMaya_root_path
            
            try:
                # kill any mMaya (2.0) that may be existing
                #
                __main__.mMaya_root_obj.kill()# > will pretty much just mMaya_root_GUIObj.kill(), at this stage of dev
                
                # expunge the current
                # such that, the current mMaya_root version is only existing in memory now as this very mMaya_root_obj that just expunged the modules used to create itself
                #
                __main__.mMaya_root_obj.expungeLoadedVer(
                    'mMaya_root',
                    isKit = False,
                    versionsPath_rootRel = 'mMaya_root_versions'
                )
                
            except:
                # maybe it was a mal install?
                #
                notGoingToWork_reboot = True
                
            else:
                
                try:
                    mMaya_root_bootVer_optVar = 'mMaya_root_bootVer'
                    cmds.optionVar(remove = mMaya_root_bootVer_optVar)# so new install path can be sniffed anew
                except:
                    # odd..
                    notGoingToWork_reboot = True
                else:
                    # rem cur from sys, make way for new path
                    #
                    try:
                        sys.path.remove(curInstallPath)
                    except:
                        notGoingToWork_reboot = True
            
            if notGoingToWork_reboot:
                cmds.confirmDialog(
                    tite = 'reboot required',
                    message = 'Maya needs to be restarted for new mMaya installation to boot correctly',
                    button = 'ok'
                )
                return
        '''
        
        cmds.optionVar(iv = ('mMaya_postInstallFirstInit', True))
        open((self.installPath+ '/mMaya/instInf'), 'w').write((self.installerUser+ ',' +str(uuid.getnode())))
        
        self.reqReboot = reqReboot
        self.installProgress = 'completeInstall, complete.'
    
    
    def mMayaInstall_editUserSet(self, test = True):
        
        
        
        
        curContent = open(self.userSetup_filePath, 'r').readlines()
        mod = ''
        alreadyPresent = False
        for line in curContent:
            
            if ('import mMaya; mMaya.init()' in line) or ('import mMaya_root; mMaya_root.boot' in line):
                if not line.strip().startswith('//'):
                    line = line.replace('python', '//python')
            
            if 'import mMaya_rootEnv; mMaya_rootEnv.init()' in line:
                if self.installPath in line:
                    if not line.strip().startswith('//'):
                        alreadyPresent = True
                else:
                    if not line.strip().startswith('//'):
                        line = line.replace('python', '//python')
            
            mod += line
        
        if not alreadyPresent:
            
            
            mod += ('\n' +self.userSetup_initEntry+ '\n\n')
        
        if test:
            
            return mod
            
        else:
            
            if not alreadyPresent:
                
                try:
                    
                    open(self.userSetup_filePath, 'w').write(mod)
                    return True
                    
                except:
                    
                    print '>> unable to write userSetup.mel:', self.userSetup_filePath
                    print 'cur content:', open(self.userSetup_filePath, 'r').read()
                    cmds.confirmDialog(
                        title = 'unable to write userSetup.mel',
                        message = ('Unable to write into userSetup.mel.\n\nThis will prevent mMaya from being able to boot each Maya session. Check write permissions on the path and try again. Installation aborted.\n\nYour userSetup.mel is currently located here:\n\n' +self.userSetup_filePath+ '\n\n'),
                        button = 'ok'
                    )
                    self.cancelInstall()
                    return False
                
            else:
                
                return True
    
    
    def build_userSetupMod_layoutDialog(self):
        
        layForm = cmds.setParent(q = True)
        layWin = cmds.layout(layForm, q = True, p = True)
        cmds.window(layWin, e = True, title = 'mMaya install, userSetup.mel modification')
        
        
        cmds.setParent(layForm)
        textScrollHeaders_fmL = cmds.formLayout()
        if 1:
            cmds.setParent(textScrollHeaders_fmL)
            unMod_txt = cmds.text(label = '- unmodified - ', align = 'center')
            cmds.setParent(textScrollHeaders_fmL)
            mod_txt = cmds.text(label = '- mMaya line appended (at end) - ', align = 'center')
            
            cmds.formLayout(textScrollHeaders_fmL, e = True,
                af = (
                    (unMod_txt, 'top', 0),
                    (unMod_txt, 'bottom', 0),
                    (unMod_txt, 'left', 0),
                    
                    (mod_txt, 'top', 0),
                    (mod_txt, 'bottom', 0),
                    (mod_txt, 'right', 0),
                ),
                ap = (
                    (unMod_txt, 'right', 2, 50),
                    (mod_txt, 'left', 2, 50),
                )
            )
        
        
        cmds.setParent(layForm)
        textScrolls_fmL = cmds.formLayout()
        if 1:
            cmds.setParent(textScrolls_fmL)
            unMod_scrlFld = cmds.scrollField(
                text = open(self.userSetup_filePath, 'r').read()
            )
            
            cmds.setParent(textScrolls_fmL)
            mod_scrlFld = cmds.scrollField(
                text = self.mMayaInstall_editUserSet(test = True)
            )
            
            cmds.formLayout(textScrolls_fmL, e = True,
                af = (
                    (unMod_scrlFld, 'top', 0),
                    (unMod_scrlFld, 'bottom', 0),
                    (unMod_scrlFld, 'left', 0),
                    
                    (mod_scrlFld, 'top', 0),
                    (mod_scrlFld, 'bottom', 0),
                    (mod_scrlFld, 'right', 0),
                ),
                ap = (
                    (unMod_scrlFld, 'right', 2, 50),
                    (mod_scrlFld, 'left', 2, 50),
                )
            )
        
        cmds.setParent(layForm)
        btns_fmL = cmds.formLayout()
        if 1:
            
            cmds.setParent(btns_fmL)
            commit_btn = cmds.button(
                label = 'looks good, write it and proceed',
                h = 40,
                c = lambda dummy: cmds.layoutDialog(dismiss = 'commitUserSetupEdit')
            )
            cmds.setParent(btns_fmL)
            cancel_btn = cmds.button(
                label = 'cancel installation',
                h = 40,
                c = lambda dummy: cmds.layoutDialog(dismiss = 'cancelInstall')
            )
            
            cmds.formLayout(btns_fmL, e = True,
                af = (
                
                    (cancel_btn, 'top', 0),
                    (cancel_btn, 'bottom', 0),
                    (cancel_btn, 'left', 0),
                    
                    (commit_btn, 'top', 0),
                    (commit_btn, 'bottom', 0),
                    (commit_btn, 'right', 0),
                    
                ),
                ap = (
                    (commit_btn, 'left', 2, 50),
                    (cancel_btn, 'right', 2, 50),
                )
            )
        
        cmds.formLayout(layForm, e = True,
            af = (
                
                (textScrollHeaders_fmL, 'top', 0),
                (textScrollHeaders_fmL, 'left', 0),
                (textScrollHeaders_fmL, 'right', 0),
                
                (textScrolls_fmL, 'left', 0),
                (textScrolls_fmL, 'right', 0),
                
                (btns_fmL, 'bottom', 0),
                (btns_fmL, 'left', 0),
                (btns_fmL, 'right', 0),
            ),
            ac = (
                (textScrolls_fmL, 'top', 5, textScrollHeaders_fmL),
                (textScrolls_fmL, 'bottom', 5, btns_fmL),
            )
        )
        
    
    def clearScene(self):
        
        sceneName = cmds.file(q = True, sceneName = True)
        
        
        
        clearSceneForMe = 'ok, clear scene for me now'
        resp = None
        if sceneName:
            resp = cmds.confirmDialog(
                title = 'new scene required',
                message = 'In order to check for and swap to updates, you must clear the scene.\n\n(ie, File > New Scene, and no edits to that).\n',
                button = ('ok', clearSceneForMe)
            )
        else:
            
            
            freshSceneBeenMod = cmds.file(q = True, modified = True)
            if freshSceneBeenMod:
                resp = cmds.confirmDialog(
                    title = 'new scene required',
                    message = 'In order to check for and swap to updates, you must have an untouched new scene.\n\n(ie, File > New Scene, and no edits to that).\n',
                    button = ('ok', clearSceneForMe)
                )
        
        if resp:
            if resp == clearSceneForMe:
                cmds.file(new = True, f = True)
            else:
                return False
        
        return True
    
    
    def passTxtFldObsc_CB(self, curChars):
        
        if self.clarafiPassStarEdit: return
        
        nbChars = len(curChars)
        curPass_nbChar = len(self.clarafiPassEntered)
        if curPass_nbChar > nbChars:
            
            
            self.clarafiPassEntered = self.clarafiPassEntered[:nbChars]
        else:
            if (nbChars - 1) > curPass_nbChar:
                
                
                
                if curPass_nbChar:
                    
                    
                    
                    self.clarafiPassEntered = ''
                    
                    self.clarafiPassStarEdit = True
                    cmds.textFieldGrp(self.clarafiPass_txtFldGrp, e = True, text = '')
                    self.clarafiPassStarEdit = False
                    
                    cmds.confirmDialog(
                        title = 'copy-paste',
                        message = 'It appears that characters were copy-pasted in to the password field. This may only be done if the field is completely clear prior. Try again, or enter password directly',
                        button = 'ok'
                    )
                    
                    return
                
                else:
                    
                    
                    self.clarafiPassEntered = curChars
                    
                
            elif nbChars == curPass_nbChar:
                pass
                
                
            else:
                
                
                self.clarafiPassEntered += curChars[-1]
        
        
        
        
        self.clarafiPassStarEdit = True
        cmds.textFieldGrp(self.clarafiPass_txtFldGrp, e = True, text = '*'*nbChars)
        self.clarafiPassStarEdit = False
    
    
    def loginUserToInitInstall(self):
        
        clarafiUser = cmds.textFieldGrp(self.clarafiUser_txtFldGrp, q = True, text = True)
        clarafiPass = self.clarafiPassEntered
        
        if clarafiUser == '':
            cmds.confirmDialog(
                title = 'no username',
                message = ('Please enter a Clarafi username'),
                button = 'ok'
            )
            return
        if clarafiPass == '':
            cmds.confirmDialog(
                title = 'no password',
                message = ('Please enter a Clarafi username password'),
                button = 'ok'
            )
            return
        
        
        mm_serv_addr = 'https://52.11.112.240/mm_serv/'
        
        post_data = urllib.urlencode(
            dict(
                clarafi_user = clarafiUser,
                clarafi_pass = clarafiPass,
                mMayaInstallLogin = True,
                mMayaInstallHWId = uuid.getnode()
            )
        )
        
        
        req = urllib2.Request(mm_serv_addr, post_data)
        try:
            
            
            cmds.waitCursor(state = True)
            
            if pyVer_2711Plus:
                import ssl
                mm_serv_response = urllib2.urlopen(req, context = ssl._create_unverified_context())
            else:
                mm_serv_response = urllib2.urlopen(req)
            
        except Exception as e:
            
            cmds.waitCursor(state = False)
            
            print 'outbound connectivity issue:', e
            
            cmds.confirmDialog(
                title = 'connectivity issue',
                message = ('There appears to be an issue connecting out to server. Please try again in a while. If problems persist, please send us feedback so we can help fix the problem, or head over to clarafi.com for more support.\n\nError code: ' +str(e)+ '\n'),
                button = 'ok'
            )
            
            return
            
        else:
            
            cmds.waitCursor(state = False)
        
        
        if mm_serv_response.code != 200:
            
            print 'server issue, not responding 200 ok:', mm_serv_response.code
            
            cmds.confirmDialog(
                title = 'server issue',
                message = ('The server appears to be having a problem. Please try again in a while. If problems persist, please send us feedback so we can help fix the problem, or head over to clarafi.com for more support.\n\nError code: ' +str(mm_serv_response.code)+ '\n'),
                
                button = 'ok'
            )
            
            return
        
        
        try:
            
            mm_serv_response_content = mm_serv_response.read()
            
        except Exception as e:
            
            
            
            print 'issue with mm_serv_response.read():', e
            
            cmds.confirmDialog(
                title = 'connectivity issue',
                message = ('There appears to be an issue retrieving results from server. Please try again in a while. If problems persist, please send us feedback so we can help fix the problem, or head over to clarafi.com for more support.\n\nError code: ' +str(e)+ '\n'),
                button = 'ok'
            )
            
            return
        
        
        if mm_serv_response_content == '':
            
            print 'issue with mm_serv_response.read() - its empty'
            
            cmds.confirmDialog(
                title = 'empty server response',
                message = ('There appears to be an issue retrieving results from server. Please try again in a while. If problems persist, please send us feedback so we can help fix the problem, or head over to clarafi.com for more support.'),
                button = 'ok'
            )
            
            return
        
        
        
        
        if mm_serv_response_content.startswith('mm_serv_error'):
            
            
            
            if mm_serv_response_content == 'mm_serv_error_S3UpdatesTmpLock':
                
                print 'mMaya serv temporarily offline as its updated'
                
                cmds.confirmDialog(
                    title = 'server update',
                    message = 'The mMaya server is being updated, check back in just a moment.',
                    button = 'ok'
                )
                
            elif mm_serv_response_content == 'mm_serv_error_invalidClarafiUsername':
                
                cmds.confirmDialog(
                    title = 'non existant user',
                    message = 'The entered username doesnt appear to exist. Try entering it again. If problems persist, head over to clarafi.com for user related questions, password reset, etc.',
                    button = 'ok'
                )
                
                
            
            elif mm_serv_response_content == 'mm_serv_error_incorrectClarafiUsernamePassword':
                
                cmds.confirmDialog(
                    title = 'incorrect password',
                    message = 'Password entered for user is incorrect. Try entering it again. If problems persist, head over to clarafi.com for user related questions, password reset, etc.',
                    button = 'ok'
                )
                
                self.clarafiPassEntered = ''
                
                self.clarafiPassStarEdit = True
                cmds.textFieldGrp(self.clarafiPass_txtFldGrp, e = True, text = '')
                self.clarafiPassStarEdit = False
                
                cmds.setFocus(self.clarafiPass_txtFldGrp)
                
            else:
                
                print mm_serv_response_content
                
                cmds.confirmDialog(
                    title = 'connectivity issue',
                    
                    message = 'There appears to be an issue connecting to server. Please try again in a while. If problems persist, please send us feedback so we can fix the problem, or head over to clarafi.com for more support.',
                    button = 'ok'
                )
            
            return
        
        else:
            
            
            
            if mm_serv_response_content == 'mm_serv_installGoAhead':
                self.installerUser = clarafiUser
                cmds.layoutDialog(dismiss = 'happyCampers')
                '''
                    Dear "malicious intent" script reader,
                        Yeah, go on, take money/info/time from a small, independent organisation that does what it does to help humans do the good stuff that they do, better.
                        For those that dont have such intent... yeah, this is about as soft as it gets w/o spending time on a next click up compiled/hidden method.
                '''
            else:
                print 'mm_serv, unhappyCamper user login response'
                cmds.confirmDialog(
                    title = 'logged in',
                    message = 'You were able to login successfully with supplied credentials, however the server appears unhappy with them. Please try again in a while. If problems persist, please send us feedback so we can fix the problem, or head over to clarafi.com for more support.',
                    button = 'ok'
                )
                cmds.layoutDialog(dismiss = 'unhappyCamper')
    
    
    def build_clarafiLoginWin(self):
        
        layDog_fmL = cmds.setParent(q = True)
        layDog_win = cmds.layout(layDog_fmL, q = True, p = True)
        cmds.window(layDog_win, e = True,
            title = 'Clarafi.com user credentials'
        )
        
        cmds.setParent(layDog_fmL)
        if 1:
            
            cmds.text(label = 'In order to install Molecular Maya you must be a member of Clarafi.')
            
            self.login_tabL = cmds.tabLayout()
            if 1:
                login_formL = cmds.formLayout(); cmds.tabLayout(self.login_tabL, e = True, tl = (login_formL, 'Clarafi secure login'))
                if 1:
                    
                    self.clarafiUser_txtFldGrp = cmds.textFieldGrp(
                        label = 'username : ',
                    )
                    
                    self.clarafiPass_txtFldGrp = cmds.textFieldGrp(
                        label = 'password : ',
                        textChangedCommand = lambda curChars: self.passTxtFldObsc_CB(curChars),
                        
                    )
                    
                    loginAndInitInstall_btn = cmds.button(
                        label = 'login, to proceed with install',
                        h = 40,
                        c = lambda dummy: self.loginUserToInitInstall(),
                    )
                    
                    visitSite_btn = cmds.button(
                        label = 'visit Clarafi.com',
                        h = 20,
                        c = lambda dummy: cmds.showHelp('https://clarafi.com', absolute = True),
                    )
                    
                    cancelInstall_btn = cmds.button(
                        label = 'cancel install',
                        h = 20,
                        c = lambda dummy: cmds.layoutDialog(dismiss = 'clarafiLoginAbort'),
                    )
                    
                    
                    self.attachFormChildren_columnStyle(login_formL, 5, 5, attachLastToBottom = True)
            
            self.attachFormChildren_columnStyle(layDog_fmL, 20, 20, attachLastToBottom = True)
            
            cmds.setFocus(self.clarafiUser_txtFldGrp)
    
    
    def build_installerGUI(self):
        
        self.win = cmds.window(
            title = 'install',
            
            
            
            w = 270,
        )
        
        os = cmds.about(os = True)
        unspportedOS = (os not in self.supportedOSs)
        
        baseForm_fmL = cmds.formLayout()
        if 1:
            
            if unspportedOS:
                
                cmds.text(
                    label = '\nMolecular Maya toolkit installation\n',
                    
                    bgc = (0.2, 0.25, 0.25)
                )
                
                cmds.separator(h = 10, style = 'none')
                
                cmds.text(
                    label = ('Sorry, mMaya is currently not supported under your current OS (' +os+ ').\nFeel free to mail us at mMaya@clarafi.com if you are keen to have this, and should\n we receive enough indications of interest we will endeavour to support it.\n\n Thanks, Clarafi Team.\n'),
                )
                
                cmds.button(
                    label = 'cancel',
                    c = lambda dummy: cmds.deleteUI(self.win)
                )
                
                cmds.separator(h = 10, style = 'none')
                
            else:
                
                cmds.text(
                    label = '\nMolecular Maya toolkit installation\n',
                    
                    bgc = (0.2, 0.25, 0.25)
                )
                
                cmds.separator(h = 10, style = 'none')
                
                self.initInstallPrompt_txt = cmds.text(label = '> start install', enable = True)
                self.installationPath_txt = cmds.text(label = 'installation path ', enable = False)
                self.downloadInProgress_txt = cmds.text(label = 'download install package', enable = False)
                self.packageExplosionInProgress_txt = cmds.text(label = 'install package', enable = False)
                self.usersetupEditPrompt_txt = cmds.text(label = 'edit userSetup', enable = False)
                
                self.installComplete_txt = cmds.text(label = 'completion', enable = False)
                
                cmds.separator(h = 10, style = 'none')
                
                cmds.setParent(baseForm_fmL)
                self.initInstallBtns_fmL = cmds.formLayout()
                if 1:
                    self.startInstall_btn = cmds.button(
                        label = 'start',
                        c = lambda dummy: self.initInstall_installationPath()
                    )
                    self.cancelInstall_btn = cmds.button(
                        label = 'cancel',
                        c = lambda dummy: self.cancelInstall()
                    )
                    
                    cmds.formLayout(self.initInstallBtns_fmL, e = True,
                        af = (
                            (self.startInstall_btn, 'top', 0),
                            (self.startInstall_btn, 'bottom', 0),
                            (self.startInstall_btn, 'left', 0),
                            
                            (self.cancelInstall_btn, 'top', 0),
                            (self.cancelInstall_btn, 'bottom', 0),
                            (self.cancelInstall_btn, 'right', 0),
                        ),
                        ap = (
                            (self.startInstall_btn, 'right', 2, 50),
                            (self.cancelInstall_btn, 'left', 2, 50),
                        )
                    )
                
                cmds.setParent(baseForm_fmL)
                cmds.separator(h = 5, style = 'none')
            
            self.attachFormChildren_columnStyle(baseForm_fmL, 5, 5)
        
        cmds.showWindow(self.win)
    
    
    def cmdRepWin(self):
        
        cmdRep = 'mMaya_cmdRep'
        cmdRepWinName = (cmdRep+ 'Win')
        if not cmds.window(cmdRepWinName, exists = True):
            cmds.window(cmdRepWinName)
            cmds.formLayout()
            cmds.cmdScrollFieldReporter(cmdRep)
        
        cmds.cmdScrollFieldReporter(cmdRep, e = True, lineNumbers = True)
        cmds.cmdScrollFieldReporter(cmdRep, e = True, stackTrace = False)
        cmds.cmdScrollFieldReporter(cmdRep, e = True, suppressStackTrace = True)
    
    def attachFormChildren_columnStyle(self, formL, stackOffset, sidesOffset, attachLastToBottom = False):
        
        stackOffset = str(stackOffset)
        sidesOffset = str(sidesOffset)
        
        formKids = cmds.layout(formL, q = 1, ca = 1)
        if formKids:
            nbKids = len(formKids)
            if nbKids != 0:
                
                lastKid = ''
                first = 1
                
                cmdStr = 'formLayout -e '
                for formKid in formKids:
                    
                    cmdStr += (' -af ' +formKid+ ' left ' +sidesOffset+ ' ')
                    cmdStr += (' -af ' +formKid+ ' right ' +sidesOffset+ ' ')
                    
                    if first:
                        first = 0
                        cmdStr += (' -af ' +formKid+ ' top ' +sidesOffset)
                    else:
                        cmdStr += (' -ac ' +formKid+ ' top ' +stackOffset+ ' ' +lastKid)
                    
                    lastKid = formKid
                
                if attachLastToBottom:
                    cmdStr += (' -af ' +lastKid+ ' bottom ' +sidesOffset)
                else:
                    cmdStr += (' -an ' +lastKid+ ' bottom ')
                
                cmdStr += (' ' +formL)
                
                mel.eval(cmdStr)
    
