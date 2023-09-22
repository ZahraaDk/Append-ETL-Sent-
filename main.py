import hook
import prehook

is_full_refresh = True

prehook.execute_prehook()
hook.execute_hook(is_full_refresh)
