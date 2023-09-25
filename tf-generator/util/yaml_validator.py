## YAML Validator
##
## Provides functionality to ensure that the YAML file matches the syntax
## requirements.
##
## Worked on: 22.09.2023, 24.09.2023

##  STEPS:
##    * Import File
##    * Read File
##    * Check File (ensure required fields are present with reasonable values)
##    * Output Validation Results


valid = True # Boolean variable for the validity of the YAML file. Set to True to avoid logic errors.
validtext = "invalid" # Text to display the validity of the YAML file.
##line_number = 0

# Boolean variables to confirm the presence of the required fields.
region_present = False
cluster_name_present = False
node_group_name_present = False
instance_type_present = False
min_size_present = False
max_size_present = False
resource_owner_present = False


# Open the YAML file and read it in line by line.
yaml_file = open("config.yml")
##print(yaml_file.read())

for line in yaml_file:
##    line_number += 1
##    print(line_number)
    print(line) # stub for testing


    # Search for region field until found.
    if region_present == False:
        region_line = line.find("aws_region:")
##        print(region_line) # stub for testing

    # Search for cluster name field until found.
    if cluster_name_present == False:
        cluster_line = line.find("cluster_name:")

    # Search for node group name field until found.
    if node_group_name_present == False:
        node_line = line.find("  - name:")

    # Search for instance type field until found.
    if instance_type_present == False:
        instance_line = line.find("    instance_type:")

    # Search for minimum size field until found.
    if min_size_present == False:
        min_line = line.find("    min_size:")

    # Search for maximum size field until found.
    if max_size_present == False:
        max_line = line.find("    max_size:")

    # Search for resource owner field until found.
    if resource_owner_present == False:
        resource_line = line.find("resource_owner:")


    # When region field is found, check to see if the field has an assigned value.
    if region_line == 0:
        region = (line[11:])
##        print(region) # stub for testing
        # If the field is empty, say so and set the YAML validity to false.
        if region.isspace():
            print("Missing region.")
            valid = False
        region_present = True # If the field is not empty, set the region presence to true.
        region_line = -1 # Set the region field back to not found to avoid unnecessarily splitting strings.

    # When cluster name field is found, check to see if the field has an assigned value.        
    if cluster_line == 0:
        cluster_name = (line[13:])
        # If the field is empty, say so and set the YAML validity to false.
        if cluster_name.isspace():
            print("Cluster is unnamed.")
            valid = False
        cluster_name_present = True # If the field is not empty, set the cluster name presence to true.
        cluster_line = -1 # Set the cluster name field back to not found to avoid unnecessarily splitting strings.

    # When node group name field is found, check to see if the field has an assigned value.
    if node_line == 0:
        node_group_name = (line[9:])
        # If the field is empty, say so and set the YAML validity to false.
        if node_group_name.isspace():
            print("Node group is unnamed.")
            valid = False
        node_group_name_present = True # If the field is not empty, set the node group name presence to true.
        node_line = -1 # Set the node group name field back to not found to avoid unnecessarily splitting strings.

    # When instance type field is found, check to see if the field has an assigned value.        
    if instance_line == 0:
        instance_type = (line[18:])
        # If the field is empty, say so and set the YAML validity to false.
        if instance_type.isspace():
            print("Node group instance type is undefined.")
            valid = False
        instance_type_present = True # If the field is not empty, set the instance type presence to true.
        instance_line = -1 # Set the instance type field back to not found to avoid unnecessarily splitting strings.

    # When minimum size field is found, check to see if the field has an assigned value.        
    if min_line == 0:
        min_size = (line[13:])
        # If the field is empty, say so and set the YAML validity to false.
        if min_size.isspace():
            print("Node group minimum size is undefined.")
            valid = False
        min_size_present = True # If the field is not empty, set the minimum size presence to true.
        min_line = -1 # Set the minimum size field back to not found to avoid unnecessarily splitting strings.

    # When maximum size field is found, check to see if the field has an assigned value.        
    if max_line == 0:
        max_size = (line[13:])
        # If the field is empty, say so and set the YAML validity to false.
        if max_size.isspace():
            print("Node group maximum size is undefined.")
            valid = False
        max_size_present = True # If the field is not empty, set the maximum size presence to true.
        max_line = -1 # Set the maximum size field back to not found to avoid unnecessarily splitting strings.

    # When resource owner field is found, check to see if the field has an assigned value.        
    if resource_line == 0:
        resource_owner = (line[15:])
        # If the field is empty, say so and set the YAML validity to false.
        if resource_owner.isspace():
            print("Resource owner is unnamed.")
            valid = False
        resource_owner_present = True # If the field is not empty, set the resource owner presence to true.
        resource_line = -1 # Set the resource owner field back to not found to avoid unnecessarily splitting strings.
        

# If everything is present, the file is set as valid.
if valid == True:
    validtext = "valid"

# The results of the validation are printed.
print("\n\n\n-+-+-+-+-+-+-+-+-+-\nThe YAML file is", validtext)
yaml_file.close()
##print("-+-+-+-+-+-\nfile closed")
    
