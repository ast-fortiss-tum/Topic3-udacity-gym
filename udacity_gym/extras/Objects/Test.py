import ObjectInterface
from udacity_gym.extras.Objects.DummyCar import DummyCar
from udacity_gym.extras.Objects.StaticBlock import StaticBlock


def print_object_attributes(obj):
    print("Name:", obj.GetName())
    print("Speed:", obj.GetSpeed() if obj.GetSpeed() is not None else "N/A")
    print("SpawnPoint:", obj.GetSpawnPoint())



if __name__ == '__main__':
    TestObject = DummyCar("Auto1", 1, 3)
    print(TestObject.GetSpawnPoint())
    TestBloc = StaticBlock("Block",  3)
    print(TestBloc.GetSpawnPoint())
    print_object_attributes(TestObject)
    print_object_attributes(TestBloc)

