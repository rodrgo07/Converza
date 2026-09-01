export type UserRole = "admin" | "manager" | "sales" | "support";

export interface User {
  id: number;
  company_id: number;
  name: string;
  email: string;
  phone?: string;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
  onboarding_completed: boolean;
  theme_preference: "light" | "dark" | "system";
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  segment?: string;
  team_size?: string;
  whatsapp_usage?: string;
  logo_url?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: number;
  company_id: number;
  name: string;
  color: string;
  created_at: string;
}

export interface CustomerTag {
  id: number;
  tag: Tag;
}

export interface Customer {
  id: number;
  company_id: number;
  name: string;
  phone: string;
  email?: string;
  company_name?: string;
  notes?: string;
  assigned_user_id?: number;
  total_spent: number;
  orders_count: number;
  last_interaction: string;
  last_purchase_date?: string;
  created_at: string;
  assigned_user?: User;
  customer_tags: CustomerTag[];
}

export type PipelineStageType = "new" | "interested" | "quote" | "negotiation" | "sale" | "post_sale" | "lost";

export interface PipelineStage {
  id: number;
  company_id: number;
  name: string;
  stage_type: PipelineStageType;
  order: number;
  color: string;
}

export interface Opportunity {
  id: number;
  company_id: number;
  customer_id: number;
  stage_id: number;
  assigned_user_id?: number;
  title: string;
  value: number;
  probability: number;
  expected_close_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  customer?: Customer;
  stage?: PipelineStage;
  assigned_user?: User;
}

export interface KanbanColumn {
  stage: PipelineStage;
  opportunities: Opportunity[];
  total_value: number;
  count: number;
}

export type MessageDirection = "inbound" | "outbound";
export type MessageType = "text" | "image" | "audio" | "document" | "video";
export type MessageStatus = "sent" | "delivered" | "read" | "failed";

export interface Message {
  id: number;
  conversation_id: number;
  sender_id?: number;
  direction: MessageDirection;
  message_type: MessageType;
  content: string;
  media_url?: string;
  status: MessageStatus;
  created_at: string;
  sender?: User;
}

export interface Conversation {
  id: number;
  company_id: number;
  customer_id: number;
  assigned_user_id?: number;
  status: string;
  unread_count: number;
  last_message_text?: string;
  last_message_time: string;
  created_at: string;
  customer?: Customer;
  assigned_user?: User;
  messages?: Message[];
}

export type FollowUpStatus = "pending" | "completed" | "expired";

export interface FollowUp {
  id: number;
  company_id: number;
  customer_id: number;
  assigned_user_id?: number;
  title: string;
  notes?: string;
  due_date: string;
  status: FollowUpStatus;
  created_at: string;
  customer?: Customer;
  assigned_user?: User;
}

export type TaskStatus = "pending" | "completed" | "cancelled";

export interface Task {
  id: number;
  company_id: number;
  customer_id?: number;
  assigned_user_id?: number;
  title: string;
  description?: string;
  due_date?: string;
  status: TaskStatus;
  created_at: string;
  customer?: Customer;
  assigned_user?: User;
}

export interface QuickReply {
  id: number;
  company_id: number;
  shortcut: string;
  title: string;
  content: string;
  created_at: string;
}

export interface WhatsAppAccount {
  id: number;
  company_id: number;
  phone_number_id?: string;
  business_account_id?: string;
  display_phone_number?: string;
  verified_name?: string;
  is_connected: boolean;
  status: string;
  webhook_verify_token: string;
  created_at: string;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}

export interface Subscription {
  id: number;
  company_id: number;
  plan: "free" | "essential" | "professional";
  status: string;
  max_users: number;
  max_customers: number;
  price_cents: number;
  current_period_end?: string;
}

export interface DashboardMetrics {
  open_conversations: number;
  new_customers_count: number;
  active_opportunities_count: number;
  total_sales_value: number;
  pending_followups_count: number;
  funnel_stages: {
    stage_id: number;
    name: string;
    color: string;
    count: number;
    value: number;
  }[];
  sales_chart_data: {
    day: string;
    vendas: number;
  }[];
  urgent_followups: FollowUp[];
  urgent_conversations: Conversation[];
}
