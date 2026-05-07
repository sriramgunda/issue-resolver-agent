# This file contains the data used for the access resolver AI.
# Users can be added to the USERS_LIST, servers can be added to the SERVER_NAMES, access types can be added to the ACCESS_TYPES, and roles can be added to the ROLES.
# User gets access to the servers based on roles and access types.
# The access types are read, write, and execute.
# The roles are admin, editor, and viewer.
# Each user assigned with a role to get access to the servers.
# The admin role has all access types, the editor role has read and write access, and the viewer role has read access only.
# APPS is a list of applications that users can have access to. Each user can have access to one or more applications.
# The USER_ACCESS dictionary contains the access information for each user, including the servers they have access to and the roles they have on those servers, as well as the applications they have access to.


USERS_LIST = ['user0001', 'user0002', 'user0003', 'user0004', 'user0005', 'user0006', 'user0007', 'user0008', 'user0009', 'user0010']

SERVER_NAMES = ['server0001', 'server0002', 'server0003', 'server0004', 'server0005', 'server0006', 'server0007', 'server0008', 'server0009', 'server0010']

ACCESS_TYPES = ['read', 'write', 'execute']

ROLES = ['admin', 'editor', 'viewer']

APPS = ['app1', 'app2', 'app3']

USER_ACCESS = {
    'user0001': {'server0001': ['admin'], 'server0002': ['editor'], 'server0003': ['viewer'], 'apps': ['app1', 'app2']},
    'user0002': {'server0002': ['admin'], 'server0004': ['editor'], 'server0005': ['viewer'], 'apps': ['app2', 'app3']},
    'user0003': {'server0003': ['admin'], 'server0006': ['editor'], 'server0007': ['viewer'], 'apps': ['app1']},
    'user0004': {'server0004': ['admin'], 'server0008': ['editor'], 'server0009': ['viewer'], 'apps': ['app2']},
    'user0005': {'server0005': ['admin'], 'server00010': ['editor'], 'server0001': ['viewer'], 'apps': ['app2', 'app3']},
    'user0006': {'server0006': ['admin'], 'server0003': ['editor'], 'server0004': ['viewer'], 'apps': ['app1', 'app3']},
    'user0007': {'server0007': ['admin'], 'server0006': ['editor'], 'server0005': ['viewer'], 'apps': ['app3']},
    'user0008': {'server0008': ['admin'], 'server0007': ['editor'], 'server0008': ['viewer'], 'apps': ['app1', 'app2']},
    'user0009': {'server0009': ['admin'], 'server00010': ['editor'], 'server0009': ['viewer'], 'apps': ['app1', 'app2']},
    'user0010': {'server0010': ['admin'], 'server0001': ['editor'], 'server0002': ['viewer'], 'apps': ['app2', 'app3']}
}
