varnames = '''
set_environment  set_video_refresh
set_audio_sample set_audio_sample_batch
set_input_poll   set_input_state
init             deinit
api_version
get_system_info  get_system_av_info
set_controller_port_device
reset            run
serialize_size   serialize
unserialize
cheat_reset      cheat_set
load_game        load_game_special
unload_game      get_region
get_memory_data  get_memory_size
'''.split()

for s in varnames:
    print("self.{} = self.retro_{}".format(s,s))
