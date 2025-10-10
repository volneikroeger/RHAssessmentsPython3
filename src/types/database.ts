export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          email: string
          full_name: string
          role: 'recruiter' | 'company' | 'admin'
          company_name: string | null
          phone: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name: string
          role: 'recruiter' | 'company' | 'admin'
          company_name?: string | null
          phone?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string
          role?: 'recruiter' | 'company' | 'admin'
          company_name?: string | null
          phone?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      talents: {
        Row: {
          id: string
          recruiter_id: string
          full_name: string
          email: string
          phone: string | null
          location: string | null
          job_title: string | null
          experience_years: number | null
          skills: string[] | null
          education: string | null
          linkedin_url: string | null
          resume_url: string | null
          status: 'active' | 'placed' | 'archived'
          notes: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          recruiter_id: string
          full_name: string
          email: string
          phone?: string | null
          location?: string | null
          job_title?: string | null
          experience_years?: number | null
          skills?: string[] | null
          education?: string | null
          linkedin_url?: string | null
          resume_url?: string | null
          status?: 'active' | 'placed' | 'archived'
          notes?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          recruiter_id?: string
          full_name?: string
          email?: string
          phone?: string | null
          location?: string | null
          job_title?: string | null
          experience_years?: number | null
          skills?: string[] | null
          education?: string | null
          linkedin_url?: string | null
          resume_url?: string | null
          status?: 'active' | 'placed' | 'archived'
          notes?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      organizations: {
        Row: {
          id: string
          name: string
          kind: 'COMPANY' | 'RECRUITER'
          subdomain: string | null
          logo_url: string | null
          primary_color: string | null
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          name: string
          kind: 'COMPANY' | 'RECRUITER'
          subdomain?: string | null
          logo_url?: string | null
          primary_color?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          name?: string
          kind?: 'COMPANY' | 'RECRUITER'
          subdomain?: string | null
          logo_url?: string | null
          primary_color?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      organization_members: {
        Row: {
          id: string
          organization_id: string
          user_id: string
          role: 'SUPER_ADMIN' | 'ORG_ADMIN' | 'HR' | 'MANAGER' | 'EMPLOYEE'
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          organization_id: string
          user_id: string
          role: 'SUPER_ADMIN' | 'ORG_ADMIN' | 'HR' | 'MANAGER' | 'EMPLOYEE'
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          organization_id?: string
          user_id?: string
          role?: 'SUPER_ADMIN' | 'ORG_ADMIN' | 'HR' | 'MANAGER' | 'EMPLOYEE'
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      employees: {
        Row: {
          id: string
          organization_id: string
          first_name: string
          last_name: string
          email: string
          phone: string | null
          job_title: string | null
          department_id: string | null
          hire_date: string | null
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          organization_id: string
          first_name: string
          last_name: string
          email: string
          phone?: string | null
          job_title?: string | null
          department_id?: string | null
          hire_date?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          organization_id?: string
          first_name?: string
          last_name?: string
          email?: string
          phone?: string | null
          job_title?: string | null
          department_id?: string | null
          hire_date?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      departments: {
        Row: {
          id: string
          organization_id: string
          name: string
          description: string | null
          manager_id: string | null
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          organization_id: string
          name: string
          description?: string | null
          manager_id?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          organization_id?: string
          name?: string
          description?: string | null
          manager_id?: string | null
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}
