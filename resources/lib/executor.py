import sys, os, urllib, ConfigParser
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

Addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))

class Main:
    _base = sys.argv[0]
    _handle = int(sys.argv[1])

    def __init__(self):
        self._parseArgs()
        self._getSettings()
        self._loadPrograms()
        self._handleArgs()

    def _parseArgs(self):
        self.params = {}
        if sys.argv[2]:
            for arg in sys.argv[2][1:].split('&'):
                unqd = urllib.unquote_plus(arg)
                try:
                    key, value = unqd.split('=', 1)
                    if value == 'None':
                        self.params[key] = None
                    else:
                        self.params[key] = value
                except:
                    self.params[unqd] = None

    def _getSettings(self):
        self.settings = {}
        self.settings['windowed'] = (Addon.getSetting('windowed') == 'true')
        self.settings['idleoff'] = (Addon.getSetting('idleoff') == 'true')

    def _handleArgs(self):
        if 'do' in self.params:
            if self.params['do'] == 'program':
                self._execProgram()
            elif self.params['do'] == 'settings':
                Addon.openSettings()
            elif self.params['do'] == 'newgui':
                self._getNewProgram()
            elif self.params['do'] == 'del':
                self._delProgram()
            elif self.params['do'] == 'add':
                self._addProgram()
        else:
            if len(self.programs) > 0:
                self._showPrograms()
            else:
                self._getNewProgram()

    def _loadPrograms(self):
        basepath = xbmc.translatePath(Addon.getAddonInfo("Profile"))
        datapath = os.path.join(basepath, "programs.cfg")

        self.programs = {}

        self.prograw = ConfigParser.RawConfigParser()
        self.prograw.read(datapath)
        for p in self.prograw.sections():
            self.programs[p] = dict(self.prograw.items(p))
            self.programs[p]['name'] = p

    def _savePrograms(self):
        basepath = xbmc.translatePath(Addon.getAddonInfo("Profile"))
        datapath = os.path.join(basepath, "programs.cfg")

        if self.prograw:
            try:
                if not os.path.exists(basepath):
                    os.makedirs(basepath)
                self.prograw.write(open(datapath, 'wb'))
            except:
                print "%s: Could not write configuration" % (self._base)

    def _rpc(self, method, params, type=None, builtin=False):
        #rpc = {'jsonrpc': '2.0', 'method': method, 'params': params}
        #return xbmc.executeJSONRPC(rpc)

        api = method + '(' + ','.join(params) + ')'

        if builtin:
            xbmc.executebuiltin(api)
            return

        value = xbmc.executehttpapi(api).replace('<li>', '')
        if type is None:
            return
        elif type == 'int':
            return int(value)
        else:
            return value

    def _execProgram(self):
        try:
            p = self.programs[self.params['id']]
        except:
            return

        idleoff = None
        windowed = None

        # Display a note that we're executing
        print "%s: executing '%s' (idle=%b, window=%b)" % (self._base, p['exec'],
                            self.settings['idleoff'], self.settings['windowed'])
        #self._rpc('XBMC.Notification', ['Executor', p['name'], '5000'], builtin=True)

        # Setup environment settings
        if self.settings['idleoff']:
            idleoff = self._rpc('GetGuiSetting', ['0', 'powermanagement.displaysoff'], type='int')
            self._rpc('SetGuiSetting', ['0', 'powermanagement.displaysoff', '0'])
        if self.settings['windowed']:
            windowed = True
            self._rpc('Action', ['199'])

        # Execute the command
        if sys.platform == 'win32':
            self._rpc('System.ExecWait', [p['exec']], builtin=True)
        elif sys.platform.startswith('linux'):
            os.system(p['exec'])
        else:
            print "%s: platform '%s' not supported" % (self._base, sys.platform)

        # Reverse environment settings
        if windowed:
            self._rpc('Action', ['199'])
        if idleoff:
            self._rpc('SetGuiSetting', ['0', 'powermanagement.displaysoff', str(idleoff)])

    def _delProgram(self):
        try:
            p = self.programs[self.params['id']]
        except:
            return

        # TODO: prompt yes/no?
        if False:
            print "%s: removing program '%s'" % (self._base, p['name'])
            if self.prograw and self.prograw.remove_section(p['name']):
                self._savePrograms()

                # TODO: force refresh list?

    def _addProgram(self):
        if self.prograw and ('name' in self.params) and ('exec' in self.params):
            print "%s: adding program '%s' exec '%s'" % (self._base,
                                self.params['name'], self.params['exec'])
            if not self.prograw.has_section(self.params['name']):
                self.prograw.add_section(self.params['name'])
            self.set(self.params['name'], 'exec', self.params['exec'])
            self._savePrograms()

            # TODO: force refresh list?

    def _showPrograms(self):
        def addMenu(self, key, item):
            return (Addon.getLocalizedString(key),
                    "XBMC.RunPlugin(%s?%s)" % (self.base, urllib.urlencode(item)))

        for p in sorted(self.programs.keys()):
            title = self.programs[p]['name']
            item = {'do': 'program', 'id': title}
            u = "%s?%s" % (self.base, urllib.urlencode(item))

            l = xbmcgui.ListItem(title)
            l.addContextMenuItems([addMenu(30102, {'do': 'del', 'id': item}),
                                   addMenu(30101, {'do': 'newgui'}),
                                   addMenu(30100, {'do': 'settings'})])
            xbmcplugin.addDirectoryItem(handle=self.hndl, url=u, listitem=l)

        xbmcplugin.endOfDirectory(handle=self.hndl, succeeded=True)

    def _getNewProgram(self):
        #TODO: show gui for program input
        pass

