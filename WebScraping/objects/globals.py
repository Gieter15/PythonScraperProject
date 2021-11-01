import os

class Globals():

    def __init__(self) -> None:
        self.objects_directory = os.getcwd()

    def get_project_abs_path(self):
        return '\\'.join(self.objects_directory.split('\\')[0:-1])

if __name__=='__main__':
    glob = Globals()
    print(glob.get_project_abs_path())