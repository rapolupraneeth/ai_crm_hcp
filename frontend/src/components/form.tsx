import { useState } from 'react';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';

function Form() {
    const formData = useSelector((state: RootState) => state.form.data);
    const [materialsFiles, setMaterialsFiles] = useState<File[]>([]);
    const [samplesFiles, setSamplesFiles] = useState<File[]>([]);

    const handleFileUpload = async (files: FileList | null, fileType: 'materials' | 'samples') => {
        if (!files || files.length === 0) return;

        const fileArray = Array.from(files);
        const formDataUpload = new FormData();

        // Assuming we have an interaction ID from the form data
        const interactionId = formData.interaction?.interaction_id;
        if (!interactionId) {
            alert('Please complete the interaction details first');
            return;
        }

        formDataUpload.append('file_type', fileType);
        fileArray.forEach(file => {
            formDataUpload.append('files', file);
        });

        try {
            const response = await fetch(`/api/v1/upload/${interactionId}`, {
                method: 'POST',
                body: formDataUpload,
            });

            if (response.ok) {
                const result = await response.json();
                alert(`Successfully uploaded ${result.files.length} files`);
                // Update local state
                if (fileType === 'materials') {
                    setMaterialsFiles(prev => [...prev, ...fileArray]);
                } else {
                    setSamplesFiles(prev => [...prev, ...fileArray]);
                }
            } else {
                alert('Failed to upload files');
            }
        } catch (error) {
            console.error('Upload error:', error);
            alert('Failed to upload files');
        }
    };

return (
  <div className="form-container">
    <h2 className="form-title">Log HCP Interaction</h2>

    {/* INTERACTION DETAILS */}
    <div className="form-card">
      <h3>Interaction Details</h3>

      <div className="form-row">
        <div className="form-field">
          <label>HCP Name</label>
          <input value={formData.hcp?.full_name || ''} readOnly />
        </div>

        <div className="form-field">
          <label>Interaction Type</label>
          <input value={formData.interaction?.interaction_type || ''} readOnly />
        </div>
      </div>

      <div className="form-row">
        <div className="form-field">
          <label>Date</label>
          <input value={formData.interaction?.date || ''} readOnly />
        </div>

        <div className="form-field">
          <label>Time</label>
          <input value={formData.interaction?.time || ''} readOnly />
        </div>
      </div>

      <div className="form-field full">
        <label>Attendees</label>
        <input value={formData.interaction?.attendees || ''} readOnly />
      </div>

      <div className="form-field full">
        <label>Topics Discussed</label>
        <textarea value={formData.interaction?.summary || ''} readOnly />
      </div>
    </div>

    {/* MATERIALS */}
    <div className="form-card">
      <h3>Materials Shared / Samples Distributed</h3>

      <div className="form-field full">
        <label>Materials Shared</label>
        <input value={formData.interaction?.materials || ''} readOnly />
        <div className="file-upload">
          <input
            type="file"
            multiple
            accept="image/*,.pdf,.csv,.xls,.xlsx,.doc,.docx,.ppt,.pptx,.txt,.zip"
            onChange={(e) => handleFileUpload(e.target.files, 'materials')}
            style={{ marginTop: '8px' }}
          />
          <small>Upload photos, documents, spreadsheets, or PDFs for materials shared</small>
        </div>
        {materialsFiles.length > 0 && (
          <div className="uploaded-files">
            <h4>Uploaded Files:</h4>
            <ul>
              {materialsFiles.map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}
        {formData.interaction?.uploaded_files?.filter(f => f.file_type === 'materials').map((file) => (
          <div key={file.id} className="uploaded-file-item">
            {file.mime_type.startsWith('image/') ? (
              <img src={`/uploads/${file.filename}`} alt={file.original_filename} style={{ maxWidth: '200px', maxHeight: '200px' }} />
            ) : (
              <a href={`/uploads/${file.filename}`} target="_blank" rel="noreferrer">{file.original_filename}</a>
            )}
            <p>{file.original_filename}</p>
          </div>
        ))}
      </div>

      <div className="form-field full">
        <label>Samples Distributed</label>
        <input value={formData.interaction?.samples || ''} readOnly />
        <div className="file-upload">
          <input
            type="file"
            multiple
            accept="image/*,.pdf,.csv,.xls,.xlsx,.doc,.docx,.ppt,.pptx,.txt,.zip"
            onChange={(e) => handleFileUpload(e.target.files, 'samples')}
            style={{ marginTop: '8px' }}
          />
          <small>Upload photos, documents, spreadsheets, or PDFs for samples distributed</small>
        </div>
        {samplesFiles.length > 0 && (
          <div className="uploaded-files">
            <h4>Uploaded Files:</h4>
            <ul>
              {samplesFiles.map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}
        {formData.interaction?.uploaded_files?.filter(f => f.file_type === 'samples').map((file) => (
          <div key={file.id} className="uploaded-file-item">
            {file.mime_type.startsWith('image/') ? (
              <img src={`/uploads/${file.filename}`} alt={file.original_filename} style={{ maxWidth: '200px', maxHeight: '200px' }} />
            ) : (
              <a href={`/uploads/${file.filename}`} target="_blank" rel="noreferrer">{file.original_filename}</a>
            )}
            <p>{file.original_filename}</p>
          </div>
        ))}
      </div>
    </div>

    {/* SENTIMENT */}
    <div className="form-card">
      <h3>Observed / Inferred HCP Sentiment</h3>

      <div className="sentiment-group">
        {['positive', 'neutral', 'negative'].map((val) => (
          <label key={val}>
            <input
              type="radio"
              checked={formData.interaction?.sentiment === val}
              readOnly
            />
            {val}
          </label>
        ))}
      </div>
    </div>

    {/* OUTCOMES */}
    <div className="form-card">
      <h3>Outcomes</h3>
      <textarea value={formData.interaction?.outcomes || ''} readOnly />
    </div>

    {/* FOLLOW-UP */}
    <div className="form-card">
      <h3>Follow-up Actions</h3>
      <textarea value={formData.follow_up?.suggestion || ''} readOnly />

      <div className="due-days">
        Due in: {formData.follow_up?.due_days || '--'} days
      </div>
    </div>

    {/* AI FOLLOWUPS */}
    <div className="form-card">
      <h3>AI Suggested Follow-ups</h3>
      <p>{formData.follow_up?.suggestion || 'No suggestions yet'}</p>
    </div>
  </div>
);
}

export default Form;