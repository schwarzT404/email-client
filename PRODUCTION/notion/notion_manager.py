#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Manager - Stub pour éviter les erreurs d'import
"""

class NotionManager:
    """Gestionnaire Notion (stub)"""
    
    def __init__(self):
        self.connected = False
        print("⚠️ NotionManager en mode stub - fonctionnalités limitées")
    
    def test_connection(self):
        """Test de connexion (stub)"""
        return False
    
    def sync_contact(self, contact_data):
        """Synchronisation contact (stub)"""
        print("⚠️ Sync Notion non disponible (mode stub)")
        return False
    
    def get_status(self):
        """Retourne le statut"""
        return {
            'connected': False,
            'mode': 'stub'
        } 