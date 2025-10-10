import React from 'react';
import { ClipboardCheck } from 'lucide-react';

export function AssessmentBuilder() {
  return (
    <div className="text-center py-12">
      <ClipboardCheck className="h-16 w-16 text-gray-400 mx-auto mb-4" />
      <h3 className="text-xl font-semibold text-gray-900 mb-2">Assessment Builder</h3>
      <p className="text-gray-600 max-w-md mx-auto">
        Create and customize psychological assessments with our intuitive builder.
        Define questions, set scoring rules, and configure assessment parameters.
      </p>
      <button className="mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        Coming Soon
      </button>
    </div>
  );
}
