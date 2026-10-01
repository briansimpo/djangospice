import tablib
from typing import Any
from dataclasses import dataclass
from djangospice.core.payload import Payload
from djangospice.jobs import Job
from djangospice.resources import BaseResource
from .dataset import TemporaryDataset 


@dataclass
class ResourceImportJob(Job):
    
    queue = "data-imports"
    resource: BaseResource
    file_path: str
    user_id: str
    raise_errors: bool = True


    def handle(self) -> dict[str, Any]:
        # 1. The Context Manager handles all IO, parsing, and guaranteed cleanup
        with TemporaryDataset(self.file_path) as dataset:
            total_rows = len(dataset)
            
            if total_rows == 0:
                return {"imported": 0, "message": "No valid data found in file."}

            batch_size = 500
            
            # 2. Process and report
            for start in range(0, total_rows, batch_size):
                end = min(start + batch_size, total_rows)
                
                # Create a chunked dataset keeping original headers
                batch = tablib.Dataset(headers=dataset.headers)
                batch.extend(dataset[start:end])

                self.resource.import_data(
                    dataset=batch, 
                    raise_errors=self.raise_errors
                )
                
                self.progress(
                    current=end,
                    total=total_rows,
                    message=f"Importing records. {self.percent}% completed."
                )
            
           
            message = f"Successfully imported {total_rows} records.",

            return Payload(total_rows=total_rows, message=message).to_dict()