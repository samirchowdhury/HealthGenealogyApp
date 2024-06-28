#!/bin/bash

# Check if the color prompt should be enabled and update .bashrc
echo 'if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then' >> ~/.bashrc
echo '    export color_prompt=yes' >> ~/.bashrc
echo 'else' >> ~/.bashrc
echo '    export color_prompt=no' >> ~/.bashrc
echo 'fi' >> ~/.bashrc

# Set up a color prompt if the terminal supports it
echo 'if [ "$color_prompt" = "yes" ]; then' >> ~/.bashrc
echo '    PS1="\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ "' >> ~/.bashrc
echo 'else' >> ~/.bashrc
echo '    PS1="\\u@\\h:\\w\\$ "' >> ~/.bashrc
echo 'fi' >> ~/.bashrc

# Ensure that the .bashrc is reloaded each time
echo 'source ~/.bashrc' >> ~/.bash_profile

# Read Anthropic API key from file and export as environment variable
if [ -f /home/pothos/anthro_api_key.txt ]; then
    export ANTHROPIC_API_KEY=$(cat /home/pothos/anthro_api_key.txt)
    echo 'export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY >> ~/.bashrc
    echo "Anthropic API key has been set as an environment variable."
else
    echo "Warning: anthro_api_key.txt file not found. ANTHROPIC_API_KEY environment variable not set."
fi

# Execute the command provided as arguments to the entrypoint (i.e., CMD in Dockerfile)
exec "$@"