# fix missing library when env variables are reloaded and container loose jsonpath. TODO: why does it happen?
import pip
pip.main(['install',"jsonpath_ng==1.4.3"])
