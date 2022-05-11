# cf-transcribe-audio-peerlogic

## 1. Resources

- how to develop and debug your application locally with [functions-framework-python](https://github.com/GoogleCloudPlatform/functions-framework-python).
- how to automate the deployment of Cloud Functions with Cloud Build on Google Cloud Platform.

Check the complete tutorial [here](https://medium.com/@ivam.santos/how-to-develop-debug-and-test-your-python-google-cloud-functions-on-your-local-dev-environment-d56ef94cb409).

## 2. Environment setup


### 2.0 Program Dependencies

- ffmpeg: `brew install ffmpeg`

### 2.1. Virtualenv

- Install Python 3.7+

- Create and activate an isolated Python environment

  ```bash
  virtualenv --python `which python3.7` venv
  source ./venv/bin/activate
  ```

- Install the dependencies

  ```bash
  pip install -r requirements-dev.txt
  pip install -r requirements.txt
  ```

## 3. Run and test the app locally

### 3.0 Place .env files
Create scripts/.env from deployments/.envexample.

### 3.1 Testing the pub/sub example

From inside root of the directory:

```bash
./scripts/run-local-pubsub.sh
```

From a different terminal window:

```bash
./scripts/test-local-pubsub.sh '{"call_id": "6fAoVoxkfCenkm2K6ejYGU", "partial_id": "bo6FTU5HbpsUmYn8TFofNq", "audio_partial_id": "a3HvzN9htW5H5j9i2X23mL"}'
```

`test-local-pubsub.sh` does the following behind the scenes:

- encodes the message passed as parameter in **base64** format;
- reads the contents of `./scripts/payloads/test-local-payload.json` and replaces its `data` property with the **base64** encoded message;
- performs an HTTP post request to `http://localhost:8080` (the default address the application runs when you execute `./scripts/run-local-pubsub.sh` from the other terminal window), sending the modified JSON from the previous step in the payload.

On the terminal window where you ran `./scripts/run-local-pubsub.sh` you should see some logs showing a message was received.

### 3.2 Testing the HTTP example

From inside root of the directory:

```bash
./scripts/run-local-http.sh
```

From a different terminal window:

```bash
./scripts/test-local-http.sh
```

`test-local-http.sh` performs a `GET` HTTP request to `http://localhost:8080/?subject=FooBar` and prints the response:

```console
$ ./test-local-http.sh
Hello, FooBar!
```

## 4. Deployment


Run `gcloud init`.

1. Re-initialize your default configuration
2. Set the project to the one you created (there can be a time delay for a newly created project to appear in the list of your organization's projects.)
3. Confirm your email login
4. Do you want to configure a default Compute Region and Zone?
   * Hit `Y` and then enter
   * Set the zone to `us-west4-a`


5. Create an environment file  `./deployment/<PROJECT_ID>.env` with the given project id.
   * Escape any funny characters in your `./deployment/<PROJECT_ID>.env` file that bash doesn't like with " " around the value after the `=` sign.
   * Lay down ./deployment/peerlogic-api-dev.env from [1Password: cf-transcribe-audio-peerlogic dev .env](https://start.1password.com/open/i?a=P3RU52IFYBEH3GKEDF2UBYENBQ&v=vpraap47l6wamzclmiyonzzfw4&i=ymljh6lpq5hrtikxg6k76rrai4&h=my.1password.com).
   * \# TODO: Create stage and prod and 1Password links.
6. Uncomment all lines in this file if running for the first time `./deployment/gcloud_deploy.bash` and then run it from the root of this repository.
