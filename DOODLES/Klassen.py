ifc_Objects = {}

class class_ifc():
    def __init__(self,UID:str,ifcType:str):
        self.UID = UID
        self.ifcType = ifcType
        self.parent = None
        self.children = []
        ifc_Objects[UID] = ifcType

    def getParent(self):
        return self.parent
    
    def getUID(self):
        return self.UID
    
    def getifcType(self):
        return self.ifcType
    
    def getChildren(self):
        return self.children

def getifcbyGUID(GUID:str):
    return ifc_Objects(GUID)

class class_socket():
    def __init__(self,socketType,ifc:class_ifc,wall=None):
        self.socketType = socketType
        self.ifc = ifc
        self.wall=wall

    def getWall(self):
        return self.wall.ifc.getUID()
    
    def getSocketType(self):
        return str(self.socketType)
    
    def assignWall(self,wall):
        self.wall=wall
        wall.addSocket(self)
    
class class_wall():
    def __init__(self,ifc:class_ifc,room=None):
        self.ifc=ifc
        self.room=room
        self.sockets=[]

    def addSocket(self,socket):
        self.sockets.append(socket)

    def asignRoom(self,room):
        self.room=room
        room.addwall(self)
    
    def getSockets(self):
        return self.sockets

class class_room():
    def __init__(self,ifc:class_ifc,name):
        self.ifc=ifc
        self.name = name
        self.walls=[]

    def getName(self):
        return self.name
    
    def addWall(self,wall:class_wall):
        self.walls.append(wall.ifc.getUID())

ifc_socket=class_ifc("123","ifcOutlet")
my_socket=class_socket("T13",ifc_socket)
print(my_socket.getSocketType())

ifc_wall=class_ifc("W01","ifcWall")
my_wall1=class_wall(ifc_wall)
ifc_wall=class_ifc("W02","ifcWall")
my_wall2=class_wall(ifc_wall)
ifc_wall=class_ifc("W03","ifcWall")
my_wall3=class_wall(ifc_wall)

ifc_room=class_ifc("789","ifcRoom")
my_Room=class_room(ifc_room,"Wohnzimmer")

print(ifc_Objects)

my_Room.addWall(my_wall1)
my_Room.addWall(my_wall3)
my_Room.addWall(my_wall2)

print(f"Die Wände von Raum {my_Room.name} sind {my_Room.walls}")
for wall in my_Room.walls:
    print(wall)
    print(getifcbyGUID(wall))