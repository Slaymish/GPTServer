from quart import Quart, request, jsonify
import asyncio
from tapo import ApiClient, Color
import os

app = Quart(__name__)

# Replace these with your actual Tapo account details
TAPO_USERNAME = "hamishapps@gmail.com"
TAPO_PASSWORD = "l1tHyr~s"
IP_ADDRESSES = {
    "kitchen_light": "192.168.68.60", # Living room, Kitchen light
    "tv_light": "192.168.68.61", # Living room, TV light
    "living_room_plug": "192.168.68.64", # Living room plug (only on/off) P100
    "desk_light": "192.168.68.54", # Jack's room, desk light
    "bed_light": "192.168.68.51" # Jack's room, bed light
}

lights = {}

@app.before_serving
async def initialize():
    global lights
    client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
    errors = {}
    for light_name, ip_address in IP_ADDRESSES.items():
        try:
            if light_name == "living_room_plug":
                lights[light_name] = await client.p100(ip_address)
            else:
                lights[light_name] = await client.l530(ip_address)
            app.logger.info(f"Connected to {light_name} successfully.")
            print(f"Connected to {light_name} successfully.")
        except Exception as e:
            app.logger.error(f"Failed to connect to {light_name} at {ip_address}. Error: {e}")
            errors[light_name] = str(e)
            lights[light_name] = None  # Set to None or some default

    if errors:
        app.logger.error(f"Failed to initialize some lights: {errors}")
        print(f"Failed to initialize some lights: {errors}")



"""
Control lights
POST /control_lights
{
    "action": "on", "off", "toggle",
    "lights": ["kitchen_light", "tv_light"]  # Optional, control specific lights
}
"""
@app.route('/control_lights', methods=['POST'])
async def control_lights():
    data = await request.get_json()
    action = data.get('action')  # "on", "off", "toggle"
    light_names = data.get('lights', lights.keys())  # Control specific or all lights
    responses = await asyncio.gather(*[
        control_light(lights[name], action) for name in light_names if name in lights
    ])
    return jsonify({"results": responses}), 200


"""
Set properties for lights
POST /set_properties
{
    "brightness": 50,  # 0-100
    "rgb": [255, 0, 0],  # Optional, RGB color
    "lights": ["kitchen_light", "tv_light"]  # Optional, set properties for specific lights
}
"""
@app.route('/set_properties', methods=['POST'])
async def set_properties():
    data = await request.get_json()
    brightness = data.get('brightness')
    rgb = data.get('rgb')  # Expecting RGB as a list [R, G, B]
    light_names = data.get('lights', lights.keys())  # Set properties for specific or all lights
    if rgb and len(rgb) == 3:
        try:
            color = Color(tuple(rgb))  # If the constructor expects a tuple
        except TypeError:
            print("Failed to instantiate Color")
            color = None

    
    # Set properties and turn on the lights
    await asyncio.gather(*[
        set_light_properties(lights[name], brightness=brightness, color=color) for name in light_names if name in lights
    ])

    return jsonify({"results": [f"{name} properties set" for name in light_names if name in lights]}), 200


"""
Get info for lights
GET /get_info?lights=kitchen_light&lights=tv_light
"""
@app.route('/get_info', methods=['GET'])
async def get_info():
    light_names = request.args.getlist('lights') or list(lights.keys())
    info_responses = []
    for name in light_names:
        if name in lights and lights[name]:
            try:
                device_info = await get_device_info(lights[name])
                info_responses.append((name, device_info))
            except Exception as e:
                app.logger.error(f"Failed to retrieve info for {name}: {e}")
                info_responses.append((name, None))
        else:
            info_responses.append((name, None))

    response_dict = {
        name: {
            'is_on': info.device_on if info else None,
            'hue': getattr(info, 'hue', None) if info else None,
            'brightness': getattr(info, 'brightness', None) if info else None
        } for name, info in info_responses
    }
    return jsonify(response_dict), 200



async def set_light_properties(device, brightness=None, color=None):
    print(f"Setting properties for {device}")
    if brightness is not None:
        if brightness > 0:
            await device.turn_on()  # Make sure to turn on the light if setting brightness
        await device.set_brightness(brightness)
    if color:
        await device.set_color(color)
    
    return f"{device} properties set"


async def control_light(device, action):
    print(f"Controlling {device} with action {action}")
    try:
        if action == "on":
            await device.on()
        elif action == "off":
            await device.off()
        elif action == "toggle":
            device_info = await device.get_device_info()
            if device_info.device_on:
                await device.off()
            else:
                await device.on()
    except Exception as e:
        if "SessionTimeout" in str(e):
            # Reinitialize the client and device
            client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
            device = await client.l530(device.ip_address)
            # Retry the action
            if action == "on":
                await device.on()
            elif action == "off":
                await device.off()
            elif action == "toggle":
                device_info = await device.get_device_info()
                if device_info.device_on:
                    await device.off()
                else:
                    await device.on()

    return f"{device} {action} successful"

async def get_device_info(device):
    print(f"Getting info for {device}")
    try:
        return await device.get_device_info()
    except Exception as e:
        if "SessionTimeout" in str(e):
            # Reinitialize the client and device
            client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
            device = await client.l530(device.ip_address)
            # Retry the get_device_info
            return await device.get_device_info()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
