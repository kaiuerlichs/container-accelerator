## YAML Validator
##
## Provides functionality to ensure that the YAML file matches the syntax
## requirements.
##
## Worked on: 22.09.2023

##  STEPS:
##    * Import File
##    * Read File
##    * Check File (ensure required fields are present with reasonable values)
##    * Output Validation Results


valid = True
validtext = "invalid"
line_number = 0

yaml_file = open("config.yml")
##print(yaml_file.read())
for line in yaml_file:
    line_number += 1
    print(line_number)
    print(line)
    if line_number == 2:
        region = (line[11:])
        if region.isspace():
            print("Missing region.")
            valid = False
            
    if line_number == 15:
        cluster_name = (line[13:])
        if cluster_name.isspace():
            print("Cluster is unnamed.")
            valid = False
            
    if line_number == 25:
        node_group_name = (line[9:])
        if node_group_name.isspace():
            print("Node group is unnamed.")
            valid = False
            
    if line_number == 26:
        instance_type = (line[18:])
        if instance_type.isspace():
            print("Node group instance type is undefined.")
            valid = False
            
    if line_number == 27:
        min_size = (line[13:])
        if min_size.isspace():
            print("Node group minimum size is undefined.")
            valid = False
            
    if line_number == 28:
        max_size = (line[13:])
        if max_size.isspace():
            print("Node group maximum size is undefined.")
            valid = False
            
    if line_number == 38:
        resource_owner = (line[15:])
        if resource_owner.isspace():
            print("Resource owner is unnamed.")
            valid = False

if valid == True:
    validtext = "valid"
    
print("\n-+-+-+-+-+-+-+-+-+-\nThe YAML file is", validtext)
yaml_file.close()
print("-+-+-+-+-+-\nfile closed")
    
