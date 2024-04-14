from quart import Quart, request, jsonify
import asyncio
from tapo import ApiClient, Color, EnergyDataInterval  # Import EnergyDataInterval
import os
import re

app = Quart(__name__)

# dot env

# Environment variables for TAPO credentials
TAPO_USERNAME = os.getenv("TAPO_USERNAME", "hamishapps@gmail.com")
TAPO_PASSWORD = os.getenv("TAPO_PASSWORD", "l1tHyr~s")
IP_ADDRESSES = {
    "kitchen_light": "192.168.68.60",
    "tv_light": "192.168.68.61",
    "living_room_plug": "192.168.68.64",
    "desk_light": "192.168.68.54",
    "bed_light": "192.168.68.51"
}

lights = {}

@app.before_serving
async def initialize_lights():
    """Initialize connections to Tapo lights."""
    global lights
    client = ApiClient(TAPO_USERNAME, TAPO_PASSWORD)
    for name, ip in IP_ADDRESSES.items():
        try:
            if 'plug' in name:
                lights[name] = await client.p100(ip)
            else:
                lights[name] = await client.l530(ip)
            app.logger.info(f"Connected to {name} at {ip} successfully.")
        except Exception as e:
            app.logger.error(f"Failed to connect to {name} at {ip}: {e}")
            lights[name] = None

"""
Control lights
POST /control_lights
{
    "action": "on",  # on, off, toggle
    "lights": ["kitchen_light", "tv_light"]  # Optional, control specific lights
}

"""
@app.route('/control_lights', methods=['POST'])
async def control_lights():
    """Control specified or all lights to turn on, off, or toggle."""
    data = await request.get_json()
    action = data.get('action')
    light_names = data.get('lights', lights.keys())

    results = await asyncio.gather(*[
        control_light(lights[name], action) for name in light_names if lights[name]
    ], return_exceptions=True)

    response = {name: f"{action} successful" if not isinstance(res, Exception) else str(res)
                for name, res in zip(light_names, results)}
    return jsonify(response), 200

"""
Set properties for lights
POST /set_properties
{
    "brightness": 50,  # 0-100
    "color": "#FF0000",  # Hex color code
    "lights": ["kitchen_light", "tv_light"]  # Optional, set properties for specific lights
}
"""
@app.route('/set_properties', methods=['POST'])
async def set_properties():
    data = await request.get_json()
    brightness = data.get('brightness')
    hex_color = data.get('color')  # Expecting color as a hex code (e.g., "#FF0000")
    light_names = data.get('lights', lights.keys())  # Set properties for specific or all lights

    color = None
    if hex_color:
        if re.match(r'^#[0-9A-Fa-f]{6}$', hex_color):  # Validate hex color code
            try:
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))  # Convert hex to RGB tuple
                app.logger.info(f"RGB values: {rgb}")
                color = Color(rgb[0], rgb[1], rgb[2])  # Create a Color object from RGB values
                app.logger.info(f"Color object: {color}")
            except Exception as e:
                print(f"Failed to parse color: {e}")
                color = None
        else:
            app.logger.error(f"Invalid color format: {hex_color}")
            return jsonify({"error": "Invalid color format. Use #RRGGBB format."}), 400

    results = await asyncio.gather(*[
        set_light_properties(lights[name], brightness=brightness, color=color, ip_address=IP_ADDRESSES[name])
        for name in light_names if name in lights  # Ensure the light exists
    ])

    response_data = {name: result for name, result in zip(light_names, results)}
    return jsonify({"response_data": response_data, "status_code": 200}), 200

@app.route('/get_info', methods=['GET'])
async def get_info():
    """Retrieve information about specified or all connected lights."""
    light_names = request.args.getlist('lights')
    if not light_names:
        light_names = list(lights.keys())

    async def get_light_info(name):
        if name in lights:
            device_info = await get_device_info(lights[name])
            if isinstance(device_info, Exception):
                return name, {"error": str(device_info)}
            else:
                return name, {
                    'is_on': device_info.device_on,
                    'hue': getattr(device_info, 'hue', None),
                    'brightness': getattr(device_info, 'brightness', None)
                }
        return name, {"error": "Light not found"}

    results = await asyncio.gather(*[get_light_info(name) for name in light_names])
    results_dict = dict(results)

    return jsonify(results_dict), 200


async def set_light_properties(device, brightness=None, color=None, ip_address=None):
    print(f"Device type for device at {ip_address}: {type(device)}") # Keep this for debugging
    print(dir(device))  # Shows available attributes and methods for the device object

    if isinstance(device, tapo.p100):  # Or the correct plug class
        # Smart Plug Logic
        if brightness is not None:
            await device.turn_on() if brightness > 0 else await device.turn_off()
    else:
        # Light Bulb Logic (assuming all other devices are lights)
        if brightness is not None:
            if brightness > 0:
                await device.turn_on()
            await device.set_brightness(brightness)
        if color is not None:
            await device.set_color(color)

    return f"Properties set for device at {ip_address}"

    

async def control_light(device, action):
    """Control a light's state to on, off, or toggle based on the action."""
    if action == "on":
        await device.on()
    elif action == "off":
        await device.off()
    elif action == "toggle":
        device_info = await device.get_device_info()
        await device.off() if device_info.device_on else await device.on()
    return "action successful"

async def get_device_info(device):
    """Retrieve the current state information of a light."""
    return await device.get_device_info()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)