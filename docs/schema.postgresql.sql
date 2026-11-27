
CREATE TABLE users (
	id VARCHAR(80) NOT NULL,
	email VARCHAR(254) NOT NULL,
	password_hash VARCHAR NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (email)
)

;


CREATE TABLE exercises (
	id VARCHAR(80) NOT NULL,
	name VARCHAR NOT NULL,
	source VARCHAR NOT NULL,
	source_commit VARCHAR NOT NULL,
	source_hash VARCHAR NOT NULL,
	data JSON NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE INDEX ix_exercises_name ON exercises (name);


CREATE TABLE achievements (
	id VARCHAR(80) NOT NULL,
	code VARCHAR NOT NULL,
	criteria JSON NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (code)
)

;


CREATE TABLE challenges (
	id VARCHAR(80) NOT NULL,
	name VARCHAR NOT NULL,
	rules JSON NOT NULL,
	PRIMARY KEY (id)
)

;


CREATE TABLE learning_models (
	id VARCHAR(80) NOT NULL,
	status VARCHAR(20) NOT NULL,
	artifact JSON NOT NULL,
	report JSON NOT NULL,
	dataset_hash VARCHAR(64) NOT NULL,
	review JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (dataset_hash)
)

;


CREATE TABLE survey_receipts (
	id VARCHAR(80) NOT NULL,
	expires_at FLOAT NOT NULL,
	PRIMARY KEY (id)
)

;

CREATE INDEX ix_survey_receipts_expires_at ON survey_receipts (expires_at);


CREATE TABLE profiles (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	data JSON NOT NULL,
	version INTEGER NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_profiles_user_id ON profiles (user_id);


CREATE TABLE goals (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	name VARCHAR(50) NOT NULL,
	priority INTEGER NOT NULL,
	PRIMARY KEY (id),
	CHECK (priority >= 0 AND priority <= 100),
	UNIQUE (user_id, name),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_goals_user_id ON goals (user_id);


CREATE TABLE api_keys (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	name VARCHAR NOT NULL,
	digest VARCHAR(64) NOT NULL,
	scopes JSON NOT NULL,
	kind VARCHAR NOT NULL,
	expires_at FLOAT NOT NULL,
	revoked BOOLEAN NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	UNIQUE (digest)
)

;

CREATE INDEX ix_api_keys_user_id ON api_keys (user_id);


CREATE TABLE exercise_metadata (
	id VARCHAR(80) NOT NULL,
	exercise_id VARCHAR(80) NOT NULL,
	data JSON NOT NULL,
	status VARCHAR NOT NULL,
	reviewer VARCHAR,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (exercise_id),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
)

;


CREATE TABLE exercise_media (
	id VARCHAR(80) NOT NULL,
	exercise_id VARCHAR(80) NOT NULL,
	kind VARCHAR NOT NULL,
	source_path VARCHAR NOT NULL,
	attribution VARCHAR NOT NULL,
	license_status VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (exercise_id, kind),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_exercise_media_exercise_id ON exercise_media (exercise_id);


CREATE TABLE exercise_relations (
	id VARCHAR(80) NOT NULL,
	exercise_id VARCHAR(80) NOT NULL,
	related_id VARCHAR(80) NOT NULL,
	kind VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (exercise_id, related_id, kind),
	FOREIGN KEY(exercise_id) REFERENCES exercises (id),
	FOREIGN KEY(related_id) REFERENCES exercises (id)
)

;


CREATE TABLE workouts (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	day VARCHAR(10) NOT NULL,
	status VARCHAR NOT NULL,
	plan JSON NOT NULL,
	version INTEGER NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id, day),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_workouts_user_id ON workouts (user_id);


CREATE TABLE readiness_logs (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_readiness_logs_user_id ON readiness_logs (user_id);


CREATE TABLE xp_transactions (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	event VARCHAR NOT NULL,
	amount INTEGER NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	CHECK (amount >= 0),
	UNIQUE (user_id, event),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_xp_transactions_user_id ON xp_transactions (user_id);


CREATE TABLE audit_logs (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	action VARCHAR NOT NULL,
	resource_id VARCHAR,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);


CREATE TABLE assessments (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_assessments_user_id ON assessments (user_id);


CREATE TABLE recovery_logs (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_recovery_logs_user_id ON recovery_logs (user_id);


CREATE TABLE pain_reports (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_pain_reports_user_id ON pain_reports (user_id);


CREATE TABLE progress_measurements (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_progress_measurements_user_id ON progress_measurements (user_id);


CREATE TABLE nutrition_profiles (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_nutrition_profiles_user_id ON nutrition_profiles (user_id);


CREATE TABLE nutrition_targets (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_nutrition_targets_user_id ON nutrition_targets (user_id);


CREATE TABLE meals (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_meals_user_id ON meals (user_id);


CREATE TABLE wearable_connections (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_wearable_connections_user_id ON wearable_connections (user_id);


CREATE TABLE wearable_measurements (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_wearable_measurements_user_id ON wearable_measurements (user_id);


CREATE TABLE camera_sessions (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_camera_sessions_user_id ON camera_sessions (user_id);


CREATE TABLE notifications (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_notifications_user_id ON notifications (user_id);


CREATE TABLE ai_interactions (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	schema_version INTEGER NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_ai_interactions_user_id ON ai_interactions (user_id);


CREATE TABLE programs (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	name VARCHAR NOT NULL,
	start_date VARCHAR(10),
	end_date VARCHAR(10),
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_programs_user_id ON programs (user_id);


CREATE TABLE learning_consent (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	enabled BOOLEAN NOT NULL,
	grant_token VARCHAR(80) NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_learning_consent_user_id ON learning_consent (user_id);


CREATE TABLE learning_examples (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	event_id VARCHAR(100) NOT NULL,
	grant_token VARCHAR(80) NOT NULL,
	source VARCHAR(20) NOT NULL,
	quality VARCHAR(20) NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	data JSON NOT NULL,
	review JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id, event_id),
	CHECK (quality IN ('pending','approved')),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_learning_examples_user_id ON learning_examples (user_id);

CREATE INDEX ix_learning_eligible ON learning_examples (user_id, quality);


CREATE TABLE learning_members (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	model_id VARCHAR(80) NOT NULL,
	grant_token VARCHAR(80) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id, model_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(model_id) REFERENCES learning_models (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_learning_members_model_id ON learning_members (model_id);

CREATE INDEX ix_learning_members_user_id ON learning_members (user_id);


CREATE TABLE learning_deployment (
	id VARCHAR(80) NOT NULL,
	model_id VARCHAR(80),
	mode VARCHAR(10) NOT NULL,
	PRIMARY KEY (id),
	CHECK (id = 'global'),
	CHECK (mode IN ('shadow','live')),
	FOREIGN KEY(model_id) REFERENCES learning_models (id) ON DELETE SET NULL
)

;


CREATE TABLE user_contributions (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	event_id VARCHAR(80) NOT NULL,
	session_id VARCHAR(80) NOT NULL,
	exercise_id VARCHAR(80) NOT NULL,
	occurred_at FLOAT NOT NULL,
	grant_token VARCHAR(80) NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	status VARCHAR(20) NOT NULL,
	data JSON NOT NULL,
	history_snapshot JSON,
	report JSON NOT NULL,
	review JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id, event_id),
	UNIQUE (user_id, session_id, exercise_id),
	CHECK (status IN ('pending','reviewed')),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
)

;

CREATE INDEX ix_user_contributions_user_id ON user_contributions (user_id);

CREATE INDEX ix_contributions_user_time ON user_contributions (user_id, occurred_at);


CREATE TABLE survey_participants (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	revoked BOOLEAN NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	UNIQUE (token_hash)
)

;

CREATE INDEX ix_survey_participants_user_id ON survey_participants (user_id);


CREATE TABLE media_license_grants (
	id VARCHAR(80) NOT NULL,
	media_id VARCHAR(80) NOT NULL,
	source_path VARCHAR NOT NULL,
	source_commit VARCHAR(40) NOT NULL,
	rights_reference VARCHAR NOT NULL,
	reviewed_by VARCHAR NOT NULL,
	expires_at FLOAT,
	revoked BOOLEAN NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(media_id) REFERENCES exercise_media (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_media_license_grants_media_id ON media_license_grants (media_id);


CREATE TABLE performance_logs (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	workout_id VARCHAR(80) NOT NULL,
	exercise_id VARCHAR(80) NOT NULL,
	event_id VARCHAR(80) NOT NULL,
	set_number INTEGER NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (user_id, event_id),
	UNIQUE (workout_id, exercise_id, set_number),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(workout_id) REFERENCES workouts (id) ON DELETE CASCADE,
	FOREIGN KEY(exercise_id) REFERENCES exercises (id)
)

;

CREATE INDEX ix_performance_logs_workout_id ON performance_logs (workout_id);

CREATE INDEX ix_performance_logs_user_id ON performance_logs (user_id);

CREATE INDEX ix_logs_user_time ON performance_logs (user_id, created_at);


CREATE TABLE recommendation_decisions (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	workout_id VARCHAR(80),
	engine_version VARCHAR NOT NULL,
	data JSON NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	FOREIGN KEY(workout_id) REFERENCES workouts (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_recommendation_decisions_user_id ON recommendation_decisions (user_id);


CREATE TABLE program_phases (
	id VARCHAR(80) NOT NULL,
	program_id VARCHAR(80) NOT NULL,
	kind VARCHAR,
	data JSON NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(program_id) REFERENCES programs (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_program_phases_program_id ON program_phases (program_id);


CREATE TABLE survey_responses (
	id VARCHAR(80) NOT NULL,
	user_id VARCHAR(80) NOT NULL,
	response_key VARCHAR(64) NOT NULL,
	revision INTEGER NOT NULL,
	payload_hash VARCHAR(64) NOT NULL,
	contribution_id VARCHAR(80),
	status VARCHAR(20) NOT NULL,
	created_at FLOAT NOT NULL,
	PRIMARY KEY (id),
	CHECK (revision > 0),
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
	UNIQUE (response_key),
	FOREIGN KEY(contribution_id) REFERENCES user_contributions (id) ON DELETE SET NULL
)

;

CREATE INDEX ix_survey_responses_user_id ON survey_responses (user_id);
