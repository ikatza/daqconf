# Set moo schema search path
from dunedaq.env import get_moo_model_path
import moo.io
moo.io.default_load_path = get_moo_model_path()

# Load configuration types
import moo.otypes

moo.otypes.load_types('dfmodules/datafloworchestrator.jsonnet')

# Import new types
import dunedaq.dfmodules.datafloworchestrator as dfo

from daqconf.core.app import App, ModuleGraph
from daqconf.core.daqmodule import DAQModule
from daqconf.core.conf_utils import Direction


#FIXME maybe one day, triggeralgs will define schemas... for now allow a dictionary of 4byte int, 4byte floats, and strings
moo.otypes.make_type(schema='number', dtype='i4', name='temp_integer', path='temptypes')
moo.otypes.make_type(schema='number', dtype='f4', name='temp_float', path='temptypes')
moo.otypes.make_type(schema='string', name='temp_string', path='temptypes')
def make_moo_record(conf_dict,name,path='temptypes'):
    fields = []
    for pname,pvalue in conf_dict.items():
        typename = None
        if type(pvalue) == int:
            typename = 'temptypes.temp_integer'
        elif type(pvalue) == float:
            typename = 'temptypes.temp_float'
        elif type(pvalue) == str:
            typename = 'temptypes.temp_string'
        else:
            raise Exception(f'Invalid config argument type: {type(pvalue)}')
        fields.append(dict(name=pname,item=typename))
    moo.otypes.make_type(schema='record', fields=fields, name=name, path=path)

#===============================================================================
def get_dfo_app(DF_CONF : dict = {},
                STOP_TIMEOUT: int = 10000,
                HOST="localhost",
                DEBUG=False):

    modules = []

    df_app_configs = [dfo.app_config(connection_uid=f"trigger_decision_{dfc.source_id}",
                                     thresholds=dfo.busy_thresholds(free=max(1, int(dfc.token_count/2)),
                                                                    busy=dfc.token_count)) for dfc in DF_CONF.values()]
    modules += [DAQModule(name = "dfo",
                          plugin = "DataFlowOrchestrator",
                          conf = dfo.ConfParams(dataflow_applications=df_app_configs,
                                                stop_timeout=STOP_TIMEOUT))]

    mgraph = ModuleGraph(modules)
    mgraph.add_endpoint("td_to_dfo", "dfo.td_connection", Direction.IN)
    mgraph.add_endpoint("triginh", "dfo.token_connection", Direction.IN)
    mgraph.add_endpoint("df_busy_signal", "dfo.busy_connection", Direction.OUT)
    for dfc in DF_CONF.values():
        mgraph.add_endpoint(f"trigger_decision_{dfc.source_id}", f"dfo.trigger_{dfc.source_id}_connection", Direction.OUT)

    dfo_app = App(modulegraph=mgraph, host=HOST, name='DFOApp')

    return dfo_app
