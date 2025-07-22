
# Função placeholder para get_lat_long
def get_lat_long(*args, **kwargs):
    print('Função get_lat_long chamada (placeholder).')
    return None

# Função placeholder para get_link
def get_link(*args, **kwargs):
    print('Função get_link chamada (placeholder).')
    return None

# Classe placeholder para get_request_infos
class get_request_infos:
    @staticmethod
    def parse_user_agent(*args, **kwargs):
        print('Função parse_user_agent chamada (placeholder).')
        return {}

    @staticmethod
    def get_request_infos(*args, **kwargs):
        print('Função get_request_infos chamada (placeholder).')
        import pandas as pd
        return pd.DataFrame([{'placeholder': True}])
