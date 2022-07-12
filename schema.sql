create table users (
id serial primary key ,
name  text not null,
password text not null,
expert bool not null,
admin bool not null
);
create table questions(
id serial primary key,
question_text text not null,
answer text  null,
asked_by_id integer not null,
expert_id integer not null
);