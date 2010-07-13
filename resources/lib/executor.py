import sys, os, urllib, ConfigParser
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

Addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))

class Interface:
    def __init__(self, base, hnd):
        self.base = base
        self.hndl = hnd

    def _addMenu(self, key, item):
        return (Addon.getLocalizedString(key),
                "XBMC.RunPlugin(%s?%s)" % (self.base, urllib.urlencode(item)))

    def _addItem(self, title, item):
        u = "%s?%s" % (self.base, urllib.urlencode(item))
        l = xbmcgui.ListItem(title)
        m = [self._addMenu(30102, {'do': 'del', 'id': item}),
             self._addMenu(30101, {'do': 'newgui'}),
             self._addMenu(30100, {'do': 'settings'})]
        l.addContextMenuItems(m) #, replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=self.hndl, url=u, listitem=l)

    def _endItems(self):
        xbmcplugin.endOfDirectory(handle=self.hndl, succeeded=True)

    def showPrograms(self, programs):
        for p in sorted(programs.keys()):
            self._addItem(programs[p]['name'],
                          {'do': 'program', 'id': programs[p]['name']})
        self._endItems()

    def getNewProgram(self):
        #TODO
        pass

class Main:
    _base = sys.argv[0]
    _handle = int(sys.argv[1])

    def __init__(self):
        self.interface = Interface(self._base, self._handle)

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
                #TODO
                pass
            elif self.params['do'] == 'del':
                #TODO
                pass
            elif self.params['do'] == 'add':
                #TODO
                pass
        else:
            if len(self.programs) > 0:
                self.interface.showPrograms(self.programs)
            else:
                self.interface.getNewProgram()

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

