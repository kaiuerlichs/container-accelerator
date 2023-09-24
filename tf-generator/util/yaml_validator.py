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

region_present = False
cluster_name_present = False
node_group_name_present = False
instance_type_present = False
min_size_present = False
max_size_present = False
resource_owner_present = False

yaml_file = open("config.yml")
##print(yaml_file.read())
for line in yaml_file:
##    line_number += 1
##    print(line_number)
    print(line)



    if region_present == False:
        region_line = line.find("aws_region:")
##        print(region_line) # stub for testing

    if cluster_name_present == False:
        cluster_line = line.find("cluster_name:")

    if node_group_name_present == False:
        node_line = line.find("  - name:")

    if instance_type_present == False:
        instance_line = line.find("    instance_type:")

    if min_size_present == False:
        min_line = line.find("    min_size:")

    if max_size_present == False:
        max_line = line.find("    max_size:")

    if resource_owner_present == False:
        resource_line = line.find("resource_owner:")


    
    if region_line == 0:
        region = (line[11:])
##        print(region) # stub for testing
        if region.isspace():
            print("Missing region.")
            valid = False
        region_present = True
        region_line = -1
            
    if cluster_line == 0:
        cluster_name = (line[13:])
        if cluster_name.isspace():
            print("Cluster is unnamed.")
            valid = False
        cluster_name_present = True
        cluster_line = -1
            
    if node_line == 0:
        node_group_name = (line[9:])
        if node_group_name.isspace():
            print("Node group is unnamed.")
            valid = False
        node_group_name_present = True
        node_line = -1
            
    if instance_line == 0:
        instance_type = (line[18:])
        if instance_type.isspace():
            print("Node group instance type is undefined.")
            valid = False
        instance_type_present = True
        instance_line = -1
            
    if min_line == 0:
        min_size = (line[13:])
        if min_size.isspace():
            print("Node group minimum size is undefined.")
            valid = False
        min_size_present = True
        min_line = -1
            
    if max_line == 0:
        max_size = (line[13:])
        if max_size.isspace():
            print("Node group maximum size is undefined.")
            valid = False
        max_size_present = True
        max_line = -1
            
    if resource_line == 0:
        resource_owner = (line[15:])
        if resource_owner.isspace():
            print("Resource owner is unnamed.")
            valid = False
        resource_owner_present = True
        resource_line = -1
        

if valid == True:
    validtext = "valid"
    
print("\n\n\n-+-+-+-+-+-+-+-+-+-\nThe YAML file is", validtext)
yaml_file.close()
##print("-+-+-+-+-+-\nfile closed")
    
