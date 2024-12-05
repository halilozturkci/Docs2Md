# Table of Contents

  - [docs/create_command.md](#docs/create_command.md)
  - [docs/demisto-sdk-docker.md](#docs/demisto-sdk-docker.md)
  - [docs/development_guide.md](#docs/development_guide.md)

## docs/create_command.md

Directory path: docs

## create-content-artifacts
Create content artifacts.

**Use-Cases**:
This command is primarily intended for internal use. During our CI/CD build process, this command creates archive files containing integrations, scripts and playbooks which are deployed to demisto instances for testing. The `content_new.zip`, `content_test.zip`, and `content_packs.zip` files are created and moved to the directory passed as an argument to the command (in a circleci build, this should be the path to the artifacts directory). In addition to creating the content archive files, this command tries to copy the `id_set.json` and `release_notes.md` files to the artifacts directory (which is passed as a command argument). The user can pass the `-p` flag to the command. This will preserve the intermediate directories created in the process of creating the content archive files (which would be useful if there is a need to inspect the files and debug).

**Arguments**:
* **-a ARTIFACTS_PATH, --artifacts_path ARTIFACTS_PATH**
The path of the directory in which you want to save the created content artifacts
* *-p, --preserve_bundles*
Flag for if you'd like to keep the bundles created in the process of making the content artifacts

**Examples**:
`demisto-sdk create -a .`
This will create content artifacts in the current directory.


## docs/demisto-sdk-docker.md

Directory path: docs

# Demisto-SDK docker

Run Demisto-SDK validations from within a docker container.

You can use this image to run Demisto-SDK commands locally or as a CI/CD process.

## Get The Docker Image

Pull the docker image with:
`docker pull demisto/demisto-sdk:<tag>`

You can find the latest tags in the docker hub:
`http://hub.docker.com/r/demisto/demisto-sdk`

## The Content Repository

To use the Demisto-SDK, ensure you have a content-like repository with Cortex XSOAR content in a structure that matches the official [XSOAR Content repo](https://github.com/demisto/content).

You can generate such a repository using the following [template](https://github.com/demisto/content-external-template)

## Mounts

Demisto-SDK uses volume mounts to run on the local content repository.
_Please note that mounting on macOS and Windows may cause slowness._

To ensure the best performance, please either:

- Use a Linux machine
- Use [Windows WSL2](https://docs.microsoft.com/en-us/windows/wsl/install)

## Environment Variable

Some commands such as `demisto-sdk upload` and `demisto-sdk run` need the following environment variables to communicate with your XSOAR Server:

- `DEMISTO_BASE_URL`  
    The URL of the XSOAR server to communicate with
- `DEMISTO_API_KEY`  
    API Key (Can be generated from XSOAR -> Settings -> API Key)
- `DEMISTO_VERIFY_SSL` (Default: true)  
    Whether to verify SSL certificates.

To pass those variables, you should add the following option:

```sh
docker run --env DEMISTO_BASE_URL="https://xsoar.com:443" <rest of the command>
```

You can also use an env file:

.env

```sh
DEMISTO_BASE_URL="https://xsoar.com:443"
DEMISTO_API_KEY="xxxxxxxxxxxxx"
```

Command:

```sh
docker run --env-file .env <rest of the command>
```

## Docker In Docker (Docker Daemon Binding)

To achieve Docker In Docker behavior. We want to bind the Docker Daemon with the following option:

- `--mount source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind`  
    Mounts the docker daemon container to use docker commands from within a docker container.

## Examples

(All examples use Cortex XSOAR's official [content repository](https://github.com/demisto/content)).

## Alias for easy usage

You can create an alias to the command by adding the following line to your shell configuration files:

```sh
alias demisto-sdk="docker run -it --rm \
--mount type=bind,source="$(pwd)",target=/content \
--mount source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind \
demisto/demisto-sdk:<tag>"
```

### Validate command

For more information about the validate command, please refer to its [documentation.](https://github.com/demisto/demisto-sdk/blob/master/demisto_sdk/commands/validate/README.md) on the [demisto-sdk repo](https://github.com/demisto/demisto-sdk).

```sh
docker run -it --rm \
--mount type=bind,source="$(pwd)",target=/content \
--mount source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind \
demisto/demisto-sdk:<tag> \
demisto-sdk validate -i Packs/ipinfo/Integrations/ipinfo_v2
```

#### Breaking down command arguments

- `docker run`  
    Creates a container (if one does not exist) and runs the following command inside it
- `-it`  
    Keep the stdin open and connects tty
- `--rm`  
    Removes the docker container when done (ommit this part to re-use the container in the future)
- `--mount type=bind,source="$(pwd)",target=/content`  
    Connects the pwd (assuming you're in content) to the container's content directory
- `--mount source=/var/run/docker.sock,target=/var/run/docker.sock,type=bind`  
Bind the docker daemon to the container to enable execute docker-from-docker.
- `demisto/demisto-sdk:\<tag>` (Replace the tag with locked version, can be found at the [Docker Hub](https://hub.docker.com/r/demisto/demisto-sdk))  
    The docker image name  
- `demisto-sdk validate -i Packs/ipinfo/Integrations/ipinfo_v2`
    The demisto-sdk command to be run inside the container


## docs/development_guide.md

Directory path: docs

## Contributing to Demisto SDK

To add functionality to the SDK you would need to perform the following steps:

### Create a new class
You will need to create a new directory under the `commands` folder which will contain the files relevant to your contribution.
Then, in a dedicated method, you will create an instance of your class in the SDK core class (in `__main__.py`) with the relevant arguments,
then invoke the command according to the user request.
For example, The `init` command, has a `init` folder within common, where the `Initiator` class resides
When this command is called, an instance of `Iniator` is created and the command is invoked.

### Add tests
All tests are run from the `tests` folder within the correlating command folder. They also run in the CircleCI build.
Also make sure your methods work from the CLI by running `python demisto_sdk <your_method>` in your local environment.

### How to run your unreleased demisto-sdk branch locally
There are 2 options:
1. Run `pip install -e .` in the terminal of your demisto-sdk repository. This will automatically sync your venev until deactivating it.
2. Run `tox -e py37` in the terminal of your demisto-sdk repository. This will update the changes you have made in your branch until now.

Now, Switch to your content repo and run commands from your unreleased demisto-sdk branch.

### How to run build using an unreleased demisto-sdk version
Push your branch and create a PR in demisto-sdk repository.
In your IDE go to content repository on a local branch.
Search for the file: **dev-requirements-py3.txt**.
There swap the line `demisto-sdk==X.X.X` with: `git+https://github.com/demisto/demisto-sdk.git@{your_sdk_branch_name}`. For example see [here](https://github.com/demisto/content/blob/ad06ef4d1bdd398ce4b70f0fd2e5eab7a772c11c/dev-requirements-py3.txt#L2).
Go to the file **config.yml** there you can find all the build steps - you can change whichever steps you want to check using demisto-sdk.
Make any other changes you want in the content repository and push - this will make CircleCI run using your localized branch of demisto-sdk and on the changes made on content repository.

### General guidelines
* The code is in python 3, we support python 3.7 and up.
* For common tools and constants we have the `common` directory. Before you add a constant or a tool, check if it already exists there.
* We use flake8 for lint. Before you commit you can run `flake8 demisto_sdk` to check your code.
* Whenever adding a functionality to the `validate` command, consider to add the possibility to the `format` command accordingly.
* Try to ask the user for the minimal amount of arguments possible. e.g: Do not ask for the file type, infer it using the `find_type` command from `tools.py`.
* Follow the arguments convention. e.g: `-i --input`, `-o --output`, `--insecure`.
* When adding a functionality, update the `.md` file of the command accordingly.

### Good Luck!

