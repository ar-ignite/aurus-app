#!/bin/bash
# Create a Django superuser with application and client ID

# Default values
USERNAME="aniruddha1"
EMAIL="admin@example.com"
PASSWORD="adminpassword"
FIRST_NAME="Admin"
LAST_NAME="User"
CREATE_DEFAULTS=true

# Display usage information
function show_usage {
    echo "Usage: $0 [options]"
    echo "Create a Django superuser with application and client ID"
    echo ""
    echo "Options:"
    echo "  -u, --username USERNAME    Superuser username (default: admin)"
    echo "  -e, --email EMAIL          Superuser email (default: admin@example.com)"
    echo "  -p, --password PASSWORD    Superuser password (default: adminpassword)"
    echo "  -f, --first-name NAME      Superuser first name (default: Admin)"
    echo "  -l, --last-name NAME       Superuser last name (default: User)"
    echo "  -a, --application-id ID    Application ID (UUID)"
    echo "  -c, --client-id ID         Client ID (UUID)"
    echo "  -d, --no-defaults          Don't create default application and client"
    echo "  -h, --help                 Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -u|--username)
            USERNAME="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -p|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -f|--first-name)
            FIRST_NAME="$2"
            shift 2
            ;;
        -l|--last-name)
            LAST_NAME="$2"
            shift 2
            ;;
        -a|--application-id)
            APPLICATION_ID="$2"
            shift 2
            ;;
        -c|--client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        -d|--no-defaults)
            CREATE_DEFAULTS=false
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Build command arguments
COMMAND="python manage.py create_superuser --username $USERNAME --email $EMAIL --password $PASSWORD"

if [ ! -z "$FIRST_NAME" ]; then
    COMMAND="$COMMAND --first-name \"$FIRST_NAME\""
fi

if [ ! -z "$LAST_NAME" ]; then
    COMMAND="$COMMAND --last-name \"$LAST_NAME\""
fi

if [ ! -z "$APPLICATION_ID" ]; then
    COMMAND="$COMMAND --application-id $APPLICATION_ID"
fi

if [ ! -z "$CLIENT_ID" ]; then
    COMMAND="$COMMAND --client-id $CLIENT_ID"
fi

if [ "$CREATE_DEFAULTS" = true ]; then
    COMMAND="$COMMAND --create-defaults"
fi

# Execute the command
echo "Executing: $COMMAND"
eval $COMMAND

echo "Superuser creation completed."