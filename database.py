def get_leader_approval(report_id):
    """
    Get the leader approval information for a specific report
    
    Args:
        report_id: The ID of the report
        
    Returns:
        dict: Leader approval information including action_by, timestamp, and comments
             or None if no leader approval found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT action_by, timestamp, comments FROM approval_logs "
            "WHERE report_id = ? AND action = 'approve_leader' "
            "ORDER BY timestamp DESC LIMIT 1",
            (report_id,)
        )
        
        result = cursor.fetchone()
        if result:
            return {
                'action_by': result[0],
                'timestamp': datetime.strptime(result[1], "%Y-%m-%d %H:%M:%S"),
                'comments': result[2]
            }
        return None
    
    except Exception as e:
        logger.error(f"Error getting leader approval for report {report_id}: {e}")
        return None
    finally:
        conn.close() 