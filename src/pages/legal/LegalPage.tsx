import React from 'react';
import { Layout } from '../../components/layout';

export function PrivacyPolicyPage() {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl border border-slate-200 p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-6">Privacy Policy</h1>
          <div className="prose max-w-none">
            <p className="text-slate-600 mb-4">
              This privacy policy outlines how we collect, use, and protect your personal information.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">
              Information We Collect
            </h2>
            <p className="text-slate-600 mb-4">
              We collect information that you provide directly to us, including when you create an account,
              use our services, or communicate with us.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">
              How We Use Your Information
            </h2>
            <p className="text-slate-600 mb-4">
              We use the information we collect to provide, maintain, and improve our services,
              as well as to communicate with you.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">Data Security</h2>
            <p className="text-slate-600 mb-4">
              We implement appropriate technical and organizational measures to protect your personal data.
            </p>
            <p className="text-sm text-slate-500 mt-8">Last updated: January 2025</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export function TermsOfServicePage() {
  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl border border-slate-200 p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-6">Terms of Service</h1>
          <div className="prose max-w-none">
            <p className="text-slate-600 mb-4">
              By using our platform, you agree to these terms of service.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">
              Use of Service
            </h2>
            <p className="text-slate-600 mb-4">
              Our platform is designed for organizational use only and should not be used for clinical diagnosis.
              You agree to use the service in compliance with all applicable laws and regulations.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">
              User Responsibilities
            </h2>
            <p className="text-slate-600 mb-4">
              You are responsible for maintaining the confidentiality of your account credentials
              and for all activities that occur under your account.
            </p>
            <h2 className="text-xl font-semibold text-slate-900 mt-6 mb-3">Limitation of Liability</h2>
            <p className="text-slate-600 mb-4">
              We provide the service "as is" without warranties of any kind. We shall not be liable
              for any indirect, incidental, or consequential damages.
            </p>
            <p className="text-sm text-slate-500 mt-8">Last updated: January 2025</p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
