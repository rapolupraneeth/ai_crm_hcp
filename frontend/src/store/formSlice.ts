import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

interface UploadedFile {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  uploaded_at: string;
  url?: string;
}

interface HCP {
  full_name?: string;
  external_id?: string;
  specialty?: string;
  organization?: string;
  city?: string;
}

interface Interaction {
  interaction_id?: number;
  interaction_type?: string;
  sentiment?: string;
  summary?: string;
  channel?: string;
  key_points?: string[];
  follow_up_required?: boolean;
  date?: string;
  time?: string;
  attendees?: string;
  materials?: string;
  samples?: string;
  outcomes?: string;
  uploaded_files?: UploadedFile[];
}

interface FollowUp {
  suggestion?: string;
  due_days?: number;
}

interface FormData {
  hcp: HCP;
  interaction: Interaction;
  follow_up: FollowUp;
  compliance_flags: string[];
}

interface FormState {
  data: FormData;
}

const initialState: FormState = {
  data: {
    hcp: {},
    interaction: {},
    follow_up: {},
    compliance_flags: [],
  },
};

const formSlice = createSlice({
  name: "form",
  initialState,
  reducers: {
    updateForm(state, action: PayloadAction<FormData>) {
      state.data = action.payload;
    },
  },
});

export const { updateForm } = formSlice.actions;
export default formSlice.reducer;