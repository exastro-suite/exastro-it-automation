# LLM Editor Features and Configuration

The LLM Editor is a feature that provides development assistance through conversation with an LLM model. Credentials for the LLM model are required to use it (for example, when using Amazon Bedrock (Claude Code)).

## Development Assistance Settings

- **Registering a configuration**: In AI selection, choose Amazon Bedrock (Claude Code) or another provider, and enter the credentials: AWS Access Key ID, AWS Secret Access Key, AWS Session Token (optional when using SSO), and AWS Region. Then configure the model selection and default model settings.
- **Deleting a configuration**: A deleted configuration cannot be restored, so exercise caution when deleting.

## Development Assistance Features

- The editor's contents can be attached when sending a message.
- Clicking a code block applies its contents to the editor (this feature is unavailable when the Exastro IT Automation endpoint protocol is HTTP).
- The entire conversation history can be downloaded as a JSON file.
