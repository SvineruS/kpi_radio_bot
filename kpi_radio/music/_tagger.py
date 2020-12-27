import asyncio


async def ffmpeg_metadata(input_bytes, duration=None, muxer='webm', **metadata):
    metadata = ' '.join(f'-metadata {k}="{v}"' for k, v in metadata.items())
    duration = f"-t {duration} " if duration else ""
    cmd = f'ffmpeg -i pipe: -c:a copy {metadata} {duration} -f {muxer} pipe:'

    process = await asyncio.create_subprocess_shell(cmd,
                                                    stdin=asyncio.subprocess.PIPE,
                                                    stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate(input_bytes)
    return stdout
