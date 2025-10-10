import React, { useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { AssessmentTaking } from '../../components/assessments/AssessmentTaking';
import { CheckCircle } from 'lucide-react';

export function TakeAssessmentPage() {
  const { token } = useParams<{ token: string }>();
  const [completed, setCompleted] = useState(false);

  if (!token) {
    return <Navigate to="/" replace />;
  }

  if (completed) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Assessment Complete!</h1>
          <p className="text-slate-600 mb-6">
            Thank you for completing the assessment. Your responses have been saved successfully.
          </p>
          <p className="text-sm text-slate-500">
            You can close this window now.
          </p>
        </div>
      </div>
    );
  }

  return <AssessmentTaking token={token} onComplete={() => setCompleted(true)} />;
}
