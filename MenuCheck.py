#---------------------------------------------------------------
# Project         : Mandrake
# Module          : rpmlint
# File            : MenuCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Mon Mar 20 07:43:37 2000
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import rpm
import re
import commands
import string
import sys
import stat

DEFAULT_VALID_SECTIONS=(
    "Configuration/Hardware",
    "Configuration/Packaging",
    "Configuration/Networking",
    "Configuration/Printing",
    "Configuration/Boot and Init",
    "Configuration/Other",
    "Applications/Development/Interpreters",
    "Applications/Development/Code generators",
    "Applications/Development/Development environments",
    "Applications/Development/Tools",
    "Applications/Sciences/Astronomy",
    "Applications/Sciences/Biology",
    "Applications/Sciences/Chemistry",
    "Applications/Sciences/Computer science",
    "Applications/Sciences/Geosciences",
    "Applications/Sciences/Mathematics",
    "Applications/Sciences/Physics",
    "Applications/Sciences/Other",
    "Applications/Communications",
    "Applications/Editors",
    "Applications/Emulators",
    "Applications/Archiving/Compression",
    "Applications/Archiving/Cd burning",
    "Applications/Archiving/Backup",
    "Applications/Archiving/Other",
    "Applications/Monitoring",
    "Applications/Publishing",
    "Terminals",
    "Applications/Shells",
    "Applications/File tools",
    "Applications/Text tools",
    "Documentation",
    "Office",
    "Networking/File transfer",
    "Networking/IRC",
    "Networking/ICQ",
    "Networking/Chat",
    "Networking/News",
    "Networking/Mail",
    "Networking/WWW",
    "Networking/Remote access",
    "Networking/Other",
    "Amusement/Adventure",
    "Amusement/Arcade",
    "Amusement/Boards",
    "Amusement/Cards",
    "Amusement/Puzzles",
    "Amusement/Sports",
    "Amusement/Strategy",
    "Amusement/Other",
    "Amusement/Toys",
    "Multimedia/Sound",
    "Multimedia/Graphics",
    "Multimedia/Video",
    "Session/Windowmanagers"
    )

class MenuCheck(AbstractCheck.AbstractCheck):
    menu_file=re.compile("^/usr/lib/menu/([^/]+)$")
    package=re.compile("\?package\((.*)\):")
    needs=re.compile("needs=(\"([^\"]+)\"|([^ \t\"]+))")
    section=re.compile("section=(\"([^\"]+)\"|([^ \t\"]+))")
    command=re.compile("command=\"?([^\" ]+)")
    valid_sections=Config.getOption("ValidMenuSections", DEFAULT_VALID_SECTIONS)
    update_menus=re.compile("update-menus")

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "MenuCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        files=pkg.files()
        pkgname=pkg[rpm.RPMTAG_NAME]
        menus=[]
        
        for f in files.keys():
            res=MenuCheck.menu_file.search(f)
            if res:
                basename=res.group(1)
                mode=files[f][0]
                if not stat.S_ISREG(mode):
                    printError(pkg, "non-file-in-menu-dir", f)
                else:
                    if basename != pkgname:
                        printWarning(pkg, "non-coherent-menu-filename", f)
                    menus.append(f)

        if len(menus) > 0:
            dir=pkg.dirName()
            if menus != []:
                postin=pkg[rpm.RPMTAG_POSTIN]
                if not postin:
                    printError(pkg, "menu-without-postin")
                else:
                    if not MenuCheck.update_menus.search(postin):
                        printError(pkg, "postin-without-update-menus")                    
                    
                postun=pkg[rpm.RPMTAG_POSTUN]
                if not postun:
                    printError(pkg, "menu-without-postun")
                else:
                    if not MenuCheck.update_menus.search(postun):
                        printError(pkg, "postun-without-update-menus")

            for f in menus:
                # remove comments and handle cpp continuation lines
                str="/lib/cpp %s%s | grep ^\?" % (dir, f)
                cmd=commands.getoutput(str)
                for line in string.split(cmd, "\n"):
                    res=MenuCheck.package.search(line)
                    if res:
                        package=res.group(1)
                        if package != pkgname:
                            printWarning(pkg, "incoherent-package-value-in-menu", package, f)
                    else:
                        printInfo(pkg, "unable-to-parse-menu-entry", line)
                    res=MenuCheck.needs.search(line)
                    if res:
                        grp=res.groups()
                        needs=string.lower(grp[1] or grp[2])
                        if needs == "x11" or needs == "text" or needs == "wm":
                            res=MenuCheck.section.search(line)
                            if res:
                                grp=res.groups()
                                section=grp[1] or grp[2]
                                if section not in MenuCheck.valid_sections:
                                    printWarning(pkg, "invalid-menu-section", section, f)
                            else:
                                printInfo(pkg, "unable-to-parse-menu-section", line)
                        else:
                            printInfo(pkg, "strange-needs", needs, f)
                    else:
                        printInfo(pkg, "unable-to-parse-menu-needs", line)

                    res=MenuCheck.command.search(line)
                    if res:
                        command=res.group(1)
                        try:
                            if command[0] == '/':
                                files[command]
                            else:
                                if not (files.has_key("/bin/" + command) or
                                        files.has_key("/usr/bin/" + command) or
                                        files.has_key("/usr/X11R6/bin/" + command)):
                                    raise KeyError, command
                        except KeyError:
                            printWarning(pkg, "menu-command-not-in-package", command)
                    else:
                        printInfo(pkg, "unable-to-parse-menu-command", line)
                        
# Create an object to enable the auto registration of the test
check=MenuCheck()

# MenuCheck.py ends here
