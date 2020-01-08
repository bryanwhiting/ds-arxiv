
from prefect import task, Flow
from prefect.engine.result_handlers import LocalResultHandler

@task(checkpoint=True, result_handler=LocalResultHandler(dir="~/.prefect"))
def print_df():
    return 'hello'

with Flow('test checkpoint') as flow:
    f = print_df()

flow.run()