-- AI Health Assistant - Oracle PL/SQL Extras
-- Triggers to auto-update the updated_at timestamp on record modification
-- Applies to: assessments, consultations

CREATE OR REPLACE TRIGGER trg_assessments_updated_at
BEFORE UPDATE ON assessments
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER trg_consultations_updated_at
BEFORE UPDATE ON consultations
FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/
