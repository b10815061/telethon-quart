def name2str(name):
    if(name == None):
        return ""
    return name


def find_client(client, client_list):
    if client in client_list:
        return client
    return -1
