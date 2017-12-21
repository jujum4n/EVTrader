echo 'Regening UI'
pyuic5 interface.ui > interface.py
echo 'Creating Resource file'
pyrcc5 -o resources.py  resources.qrc
