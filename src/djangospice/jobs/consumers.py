from djangospice.realtime.consumers import BaseConsumer
from djangospice.realtime.groups import build_group_name
from djangospice.realtime.scopes import ChannelScope


class JobConsumer(BaseConsumer):
    """
    Dedicated websocket consumer for tracking a single active job.
    Route: /ws/jobs/<job_id>/
    """

    async def on_connect(self) -> None:
        job_id = self.scope["url_route"]["kwargs"].get("job_id")

        if not job_id:
            await self.close(code=4400)  # Bad Request
            return

        # Resolve the standard ChannelScope.GROUP name for this specific job
        group_name = build_group_name(ChannelScope.GROUP, [f"job_{job_id}"])
        
        await self.subscribe(group_name)
        await self.accept()

        await self.send_data({
            "type": "connection.ready",
            "job_id": job_id
        })