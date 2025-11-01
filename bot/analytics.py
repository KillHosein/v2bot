"""
Advanced Analytics System with Chart Generation
Provides detailed insights and visualizations
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import io
from .db import query_db
from .cache_manager import cached, get_cache
from .config import logger

class AdvancedAnalytics:
    """Advanced analytics and reporting"""
    
    @staticmethod
    @cached(ttl=300, key_prefix="analytics")
    def get_overview_stats() -> Dict[str, Any]:
        """Get comprehensive overview statistics"""
        try:
            # User stats
            total_users = query_db("SELECT COUNT(*) as count FROM users", one=True)['count']
            new_users_today = query_db(
                "SELECT COUNT(*) as count FROM users WHERE DATE(join_date) = DATE('now')",
                one=True
            )['count']
            new_users_week = query_db(
                "SELECT COUNT(*) as count FROM users WHERE DATE(join_date) >= DATE('now', '-7 days')",
                one=True
            )['count']
            
            # Order stats
            total_orders = query_db("SELECT COUNT(*) as count FROM orders", one=True)['count']
            active_orders = query_db(
                "SELECT COUNT(*) as count FROM orders WHERE status IN ('active', 'approved')",
                one=True
            )['count']
            pending_orders = query_db(
                "SELECT COUNT(*) as count FROM orders WHERE status = 'pending'",
                one=True
            )['count']
            
            # Revenue stats (today, week, month)
            revenue_today = query_db(
                """SELECT COALESCE(SUM(final_price), 0) as revenue 
                   FROM orders 
                   WHERE status = 'approved' AND DATE(timestamp) = DATE('now')""",
                one=True
            )['revenue']
            
            revenue_week = query_db(
                """SELECT COALESCE(SUM(final_price), 0) as revenue 
                   FROM orders 
                   WHERE status = 'approved' AND DATE(timestamp) >= DATE('now', '-7 days')""",
                one=True
            )['revenue']
            
            revenue_month = query_db(
                """SELECT COALESCE(SUM(final_price), 0) as revenue 
                   FROM orders 
                   WHERE status = 'approved' AND DATE(timestamp) >= DATE('now', '-30 days')""",
                one=True
            )['revenue']
            
            # Conversion rate
            conversion_rate = (active_orders / total_users * 100) if total_users > 0 else 0
            
            # Top plans
            top_plans = query_db(
                """SELECT p.name, COUNT(*) as count, SUM(o.final_price) as revenue
                   FROM orders o
                   JOIN plans p ON o.plan_id = p.id
                   WHERE o.status = 'approved'
                   GROUP BY o.plan_id
                   ORDER BY count DESC
                   LIMIT 5"""
            )
            
            return {
                'users': {
                    'total': total_users,
                    'new_today': new_users_today,
                    'new_week': new_users_week
                },
                'orders': {
                    'total': total_orders,
                    'active': active_orders,
                    'pending': pending_orders
                },
                'revenue': {
                    'today': revenue_today,
                    'week': revenue_week,
                    'month': revenue_month
                },
                'metrics': {
                    'conversion_rate': round(conversion_rate, 2),
                    'avg_order_value': round(revenue_month / active_orders, 0) if active_orders > 0 else 0
                },
                'top_plans': top_plans
            }
        except Exception as e:
            logger.error(f"Analytics overview error: {e}")
            return {}
    
    @staticmethod
    def get_growth_chart_data(days: int = 30) -> Dict[str, List]:
        """Get user and revenue growth data for charts"""
        try:
            # User growth
            user_growth = query_db(
                f"""SELECT DATE(join_date) as date, COUNT(*) as count
                    FROM users
                    WHERE DATE(join_date) >= DATE('now', '-{days} days')
                    GROUP BY DATE(join_date)
                    ORDER BY date"""
            )
            
            # Revenue growth
            revenue_growth = query_db(
                f"""SELECT DATE(timestamp) as date, SUM(final_price) as revenue
                    FROM orders
                    WHERE status = 'approved' AND DATE(timestamp) >= DATE('now', '-{days} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date"""
            )
            
            return {
                'user_growth': user_growth,
                'revenue_growth': revenue_growth
            }
        except Exception as e:
            logger.error(f"Growth chart data error: {e}")
            return {'user_growth': [], 'revenue_growth': []}
    
    @staticmethod
    def get_user_cohort_analysis() -> List[Dict]:
        """Analyze user cohorts (retention analysis)"""
        try:
            cohorts = query_db(
                """SELECT 
                    strftime('%Y-%m', u.join_date) as cohort_month,
                    COUNT(DISTINCT u.user_id) as users,
                    COUNT(DISTINCT CASE WHEN o.status = 'approved' THEN u.user_id END) as converted
                   FROM users u
                   LEFT JOIN orders o ON u.user_id = o.user_id
                   GROUP BY cohort_month
                   ORDER BY cohort_month DESC
                   LIMIT 12"""
            )
            
            for cohort in cohorts:
                cohort['conversion_rate'] = round(
                    (cohort['converted'] / cohort['users'] * 100) if cohort['users'] > 0 else 0, 2
                )
            
            return cohorts
        except Exception as e:
            logger.error(f"Cohort analysis error: {e}")
            return []
    
    @staticmethod
    def get_traffic_sources() -> List[Dict]:
        """Analyze referral sources"""
        try:
            sources = query_db(
                """SELECT 
                    CASE 
                        WHEN referrer_id IS NOT NULL THEN 'Referral'
                        ELSE 'Direct'
                    END as source,
                    COUNT(*) as count
                   FROM users
                   GROUP BY source
                   ORDER BY count DESC"""
            )
            return sources
        except Exception as e:
            logger.error(f"Traffic sources error: {e}")
            return []
    
    @staticmethod
    def generate_chart(data: Dict, chart_type: str = 'line') -> io.BytesIO:
        """Generate chart image using matplotlib"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-GUI backend
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib import rcParams
            
            # Set font for Persian support
            rcParams['font.family'] = 'DejaVu Sans'
            
            fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1a1a1a')
            ax.set_facecolor('#2d2d2d')
            
            if chart_type == 'user_growth':
                dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data['user_growth']]
                counts = [d['count'] for d in data['user_growth']]
                
                ax.plot(dates, counts, color='#00ff88', linewidth=2, marker='o')
                ax.fill_between(dates, counts, alpha=0.3, color='#00ff88')
                ax.set_title('رشد کاربران', color='white', fontsize=14, pad=20)
                ax.set_xlabel('تاریخ', color='white')
                ax.set_ylabel('تعداد کاربران جدید', color='white')
                
            elif chart_type == 'revenue':
                dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data['revenue_growth']]
                revenues = [d['revenue'] for d in data['revenue_growth']]
                
                ax.bar(dates, revenues, color='#4CAF50', alpha=0.8)
                ax.set_title('درآمد روزانه', color='white', fontsize=14, pad=20)
                ax.set_xlabel('تاریخ', color='white')
                ax.set_ylabel('درآمد (تومان)', color='white')
            
            # Styling
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.2, color='white')
            
            # Format x-axis dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, facecolor='#1a1a1a')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return None
    
    @staticmethod
    def predict_revenue_next_month() -> float:
        """Simple revenue prediction based on trend"""
        try:
            # Get last 3 months revenue
            revenues = query_db(
                """SELECT strftime('%Y-%m', timestamp) as month, SUM(final_price) as revenue
                   FROM orders
                   WHERE status = 'approved' AND DATE(timestamp) >= DATE('now', '-90 days')
                   GROUP BY month
                   ORDER BY month"""
            )
            
            if len(revenues) < 2:
                return 0
            
            # Simple linear growth
            growth_rate = (revenues[-1]['revenue'] - revenues[0]['revenue']) / len(revenues)
            prediction = revenues[-1]['revenue'] + growth_rate
            
            return max(0, prediction)
            
        except Exception as e:
            logger.error(f"Revenue prediction error: {e}")
            return 0


# Helper function for formatted stats message
def format_stats_message(stats: Dict) -> str:
    """Format stats into beautiful Telegram message"""
    try:
        # Check if stats is empty or invalid
        if not stats or not isinstance(stats, dict):
            return "❌ خطا در دریافت آمار"
        
        msg = "📊 <b>آمار پیشرفته ربات</b>\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Users
        if 'users' in stats:
            msg += "👥 <b>کاربران:</b>\n"
            msg += f"   • کل: <code>{stats['users'].get('total', 0):,}</code>\n"
            msg += f"   • امروز: <code>{stats['users'].get('new_today', 0):,}</code>\n"
            msg += f"   • این هفته: <code>{stats['users'].get('new_week', 0):,}</code>\n\n"
        
        # Orders
        if 'orders' in stats:
            msg += "📦 <b>سفارشات:</b>\n"
            msg += f"   • کل: <code>{stats['orders'].get('total', 0):,}</code>\n"
            msg += f"   • فعال: <code>{stats['orders'].get('active', 0):,}</code> ✅\n"
            msg += f"   • در انتظار: <code>{stats['orders'].get('pending', 0):,}</code> ⏳\n\n"
        
        # Revenue
        if 'revenue' in stats:
            msg += "💰 <b>درآمد:</b>\n"
            msg += f"   • امروز: <code>{stats['revenue'].get('today', 0):,}</code> تومان\n"
            msg += f"   • هفته: <code>{stats['revenue'].get('week', 0):,}</code> تومان\n"
            msg += f"   • ماه: <code>{stats['revenue'].get('month', 0):,}</code> تومان\n\n"
        
        # Metrics
        if 'metrics' in stats:
            msg += "📈 <b>متریک‌ها:</b>\n"
            msg += f"   • نرخ تبدیل: <code>{stats['metrics'].get('conversion_rate', 0)}%</code>\n"
            msg += f"   • میانگین سفارش: <code>{stats['metrics'].get('avg_order_value', 0):,}</code> تومان\n\n"
        
        # Top plans
        if stats.get('top_plans'):
            msg += "🏆 <b>پرفروش‌ترین پلن‌ها:</b>\n"
            for i, plan in enumerate(stats['top_plans'][:3], 1):
                msg += f"   {i}. {plan['name']}: <code>{plan['count']}</code> فروش\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return msg
    except Exception as e:
        logger.error(f"Format stats message error: {e}")
        return "خطا در تولید آمار"
