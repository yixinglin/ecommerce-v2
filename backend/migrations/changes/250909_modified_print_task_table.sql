ALTER TABLE print_tasks
ADD COLUMN description TEXT COMMENT 'Description of the print task' AFTER file_paths,
ADD COLUMN skip INT NOT NULL DEFAULT 0 COMMENT 'Number of files to skip' AFTER description;
