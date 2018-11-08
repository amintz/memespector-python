# -----------------
# Messages
# -----------------

startup = "\n-------------------------\nMemespector Python script\n-------------------------"


# Error messages

error_head              = "\n**ERROR**\n"
warning_head            = "\t**WARNING**\n"
execution_error         = error_head + "Found error during script execution."
config_load_error       = error_head + "Could not open configuration file. It should be in the same folder as the script and named \'config.txt\'"
config_parse_error      = error_head + "Could not parse at least one of the settings from the config file. Please verify its contents carefully."
input_load_error        = error_head + "Could not open input file."
csv_dialect_error       = error_head + "Could not sniff CSV dialect. Check if delimiter has been correctly defined."
output_csv_create_error = error_head + "Could not create output CSV file."
output_gexf_create_error= error_head + "Could not create output GEXF file."
retrieve_image_error    = error_head + "Could not retrieve image."
api_error_warning       = error_head + "API returned an error. Check annotation file for more information: "

# -----------------
# InputType Constants
# -----------------

CSV = 0
TXT = 1
FOLDER = 2

# -----------------
# API Constants
# -----------------

api_url = 'https://vision.googleapis.com/v1/images:annotate?key='
