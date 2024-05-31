import ctypes
module_name = "get_game_info"

class GameInfoReader:
    coreToRomType = {
        'gambatte': 'gbc',
        'bsnes': 'snes',
        'genesis plus gx': 'genesis',
    }

    def get_gbc_game_info(self, data):
        return {
            'name': ctypes.string_at(data[0x134:0x143]).decode('ascii').rstrip()
        }

    def get_snes_game_info(self, data):
        return {
            'name': ctypes.string_at(data[0x7fC0:0x7fD5]).decode('ascii').rstrip()
        }

    def get_genesis_game_info(self, data):
        return {
            'name': " ".join(ctypes.string_at(data[0x120:0x150]).decode('ascii').split())
        }

    def get_info(self, romData, coreName):
        romType = self.coreToRomType.get(coreName.lower())
        if romType == None:
            print("Couldn't get game info because the core '{}' is unknown.".format(coreName))
            return {}

        getInfoForCore = getattr(self, "get_{}_game_info".format(romType))
        if getInfoForCore == None:
            print("Couldn't get game info since the rom type '{}' is unknown.".format(romType))
            return {}

        value = getInfoForCore(romData)
        print(value)
        return value
