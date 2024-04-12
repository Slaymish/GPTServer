# Light Control API

This API provides a simple interface to control smart lights in your home network programmatically. It is built using Quart, which is an asynchronous Python web framework.

## Requirements

- Docker
- Python 3.9 or later
- Quart
- Access to smart lights (Tapo devices)

## Building and Running the Docker Container

1. **Build the Docker Image**:

```sh
docker build -t lightcontrolapi:latest .
```

2. **Run the Docker Container**:

```sh
docker run -d -p 8080:8080 --name light_api lightcontrolapi:latest
```

### API Endpoints

The API provides the following endpoints:

**GET /get_info**: Retrieves information about all configured lights. It will return the status, brightness, and other relevant data.

**POST /control_lights**: Allows you to control the lights. You can turn lights on or off and toggle their states. The expected JSON payload is:

```json
{
  "action": "on",
  "lights": ["tv_light", "jack_desk_light"]
}
```

**POST /set_properties**: Sets the properties of one or more lights, such as brightness or color. The expected JSON payload is:

```json
{
  "brightness": 100,
  "rgb": [255, 255, 255],
  "lights": ["kitchen_light"]
}
```

### Usage

To use the API, you can send HTTP requests to the endpoints mentioned above. For example, to get information about all the lights, you would send a GET request to http://localhost:8080/get_info.
