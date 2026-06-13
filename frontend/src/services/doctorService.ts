/**
 * Doctor API Service.
 */

import api from "./api";

export interface PatientSearchResult {
  _id: string;
  user_id: string;
  full_name: string;
  has_treatment_consent: boolean;
}

export interface PatientAccessResult {
  patient: { _id: string; full_name: string; blood_group: string; allergies: string[] };
  consent: { _id: string; consent_type: string; granted_at: string; expires_at: string };
  records: Array<{
    _id: string; title: string; record_type: string; description: string;
    diagnosis_codes: string[]; symptoms: string[]; treatment_notes: string;
    created_at: string; version: number;
  }>;
  access_status: string;
}

export interface AccessDeniedResult {
  error: boolean;
  access_status: string;
  message: string;
  reason: string;
  patient_id: string;
  required_consent: string;
}

export const doctorService = {
  async searchPatients(query: string): Promise<PatientSearchResult[]> {
    const { data } = await api.get<{ patients: PatientSearchResult[] }>(
      "/doctors/patients/search",
      { params: { q: query } }
    );
    return data.patients;
  },

  async getPatientRecords(patientId: string): Promise<PatientAccessResult> {
    const { data } = await api.get<PatientAccessResult>(
      `/doctors/patients/${patientId}/records`
    );
    return data;
  },
};
