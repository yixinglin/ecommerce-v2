alter table transparency_code_print_log
        add charged INT NOT NULL comment 'Number of codes charged' AFTER action;

alter table transparency_code_print_log
        add status SMALLINT NOT NULL comment 'Status of the code' AFTER charged;

--docker exec -i mysql-db mysql -uroot -pYourPassword ecommerce_api < migrations/changes/250423_add_charged.sql