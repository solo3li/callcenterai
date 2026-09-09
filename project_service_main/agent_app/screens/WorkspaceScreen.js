import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Switch, TouchableOpacity, Modal, Dimensions } from 'react-native';
import { BarChart } from 'react-native-chart-kit';
import { Centrifuge } from 'centrifuge';
import axios from 'axios';

const screenWidth = Dimensions.get("window").width;

export default function WorkspaceScreen() {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [incomingCall, setIncomingCall] = useState(null);
  const [stats, setStats] = useState({ calls_today: 0, calls_this_week: [0,0,0,0,0,0,0] });
  const centrifugeRef = useRef(null);

  const data = {
    labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    datasets: [{ data: stats.calls_this_week }]
  };

  useEffect(() => {
    let sub = null;

    const setupRealtime = async () => {
      try {
        // 1. Fetch initial state & user ID
        const stateRes = await axios.get('http://localhost:8000/api/me/state/');
        setIsAvailable(stateRes.data.state === 'AVAILABLE');
        if (stateRes.data.analytics) setStats(stateRes.data.analytics);
        const userId = stateRes.data.user_id;

        // 2. Fetch Centrifugo JWT token
        const tokenRes = await axios.get('http://localhost:8000/api/me/centrifugo-token/');
        const token = tokenRes.data.token;

        // 3. Initialize secure Centrifugo connection
        const centrifuge = new Centrifuge('ws://localhost:8001/connection/websocket', {
          token: token
        });
        centrifugeRef.current = centrifuge;

        centrifuge.on('connected', () => setIsConnected(true));
        centrifuge.on('disconnected', () => setIsConnected(false));

        // Subscribe to secure namespace 'agent' with history and presence
        sub = centrifuge.newSubscription(`agent:user_${userId}`);
        
        sub.on('publication', function(ctx) {
            const data = ctx.data;
            if (data.type === 'incoming_transfer') {
                setIncomingCall({ caller: data.caller_id, summary: data.summary });
            }
        });

        // Optional: Listen to join/leave (Presence)
        sub.on('join', (ctx) => console.log('User joined:', ctx.info.user));
        sub.on('leave', (ctx) => console.log('User left:', ctx.info.user));

        sub.subscribe();
        centrifuge.connect();

      } catch (err) {
        console.log("Could not establish secure realtime connection. Using mock mode.");
        setStats({ calls_today: 12, calls_this_week: [10, 15, 8, 12, 5, 2, 0] });
      }
    };

    setupRealtime();

    // Mock for browser devtools testing
    if (typeof window !== 'undefined') {
      window.simulateIncomingCall = (caller, summary) => {
        setIncomingCall({ caller, summary });
      };
    }

    return () => {
      if (centrifugeRef.current) centrifugeRef.current.disconnect();
    };
  }, []);

  const handleStateChange = async (value) => {
    setIsAvailable(value);
    const newState = value ? 'AVAILABLE' : 'OFFLINE';
    try {
      await axios.patch('http://localhost:8000/api/me/state/', { state: newState });
    } catch (e) {
      console.log("State updated locally.");
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.title}>Agent Workspace</Text>
          <View style={[styles.connectionDot, { backgroundColor: isConnected ? '#48BB78' : '#F56565' }]} />
        </View>
        <View style={styles.statusContainer}>
          <Text style={styles.statusText}>{isAvailable ? 'AVAILABLE' : 'OFFLINE'}</Text>
          <Switch value={isAvailable} onValueChange={handleStateChange} />
        </View>
      </View>

      <View style={styles.dashboard}>
        <Text style={styles.chartTitle}>Calls Handled This Week</Text>
        <BarChart
          data={data}
          width={Math.min(screenWidth - 40, 600)}
          height={220}
          yAxisLabel=""
          chartConfig={chartConfig}
          verticalLabelRotation={0}
          style={styles.chart}
        />
        <Text style={styles.todayStats}>Calls Today: {stats.calls_today}</Text>
      </View>

      <Modal visible={!!incomingCall} transparent={true} animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.callCard}>
            <Text style={styles.callHeader}>Incoming Transfer</Text>
            <Text style={styles.callerId}>From: {incomingCall?.caller}</Text>
            
            <View style={styles.summaryBox}>
              <Text style={styles.summaryLabel}>AI Conversation Summary:</Text>
              <Text style={styles.summaryText}>{incomingCall?.summary}</Text>
            </View>

            <View style={styles.buttonRow}>
              <TouchableOpacity style={[styles.button, styles.acceptBtn]} onPress={() => setIncomingCall(null)}>
                <Text style={styles.buttonText}>Accept</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.button, styles.rejectBtn]} onPress={() => setIncomingCall(null)}>
                <Text style={styles.buttonText}>Reject</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const chartConfig = {
  backgroundGradientFrom: "#ffffff",
  backgroundGradientTo: "#ffffff",
  color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
  labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
  barPercentage: 0.5,
  fillShadowGradientOpacity: 1,
  decimalPlaces: 0,
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7FA', padding: 20 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 30, backgroundColor: '#FFF', padding: 15, borderRadius: 10, elevation: 2 },
  titleRow: { flexDirection: 'row', alignItems: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  connectionDot: { width: 10, height: 10, borderRadius: 5, marginLeft: 10 },
  statusContainer: { flexDirection: 'row', alignItems: 'center' },
  statusText: { marginRight: 10, fontWeight: '600', color: '#666' },
  dashboard: { backgroundColor: '#FFF', padding: 20, borderRadius: 10, alignItems: 'center', elevation: 2 },
  chartTitle: { fontSize: 18, fontWeight: '600', marginBottom: 20, color: '#444' },
  chart: { borderRadius: 10, paddingRight: 30 },
  todayStats: { marginTop: 15, fontSize: 16, color: '#666', fontWeight: '500' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  callCard: { width: Math.min(screenWidth - 40, 400), backgroundColor: '#FFF', padding: 25, borderRadius: 15, elevation: 5 },
  callHeader: { fontSize: 22, fontWeight: 'bold', color: '#E53E3E', marginBottom: 10, textAlign: 'center' },
  callerId: { fontSize: 16, color: '#555', marginBottom: 20, textAlign: 'center' },
  summaryBox: { backgroundColor: '#FFF5F5', padding: 15, borderRadius: 8, borderLeftWidth: 4, borderLeftColor: '#E53E3E', marginBottom: 25 },
  summaryLabel: { fontWeight: 'bold', color: '#C53030', marginBottom: 5 },
  summaryText: { fontSize: 15, color: '#2D3748', lineHeight: 22 },
  buttonRow: { flexDirection: 'row', justifyContent: 'space-between' },
  button: { flex: 1, padding: 15, borderRadius: 8, alignItems: 'center' },
  acceptBtn: { backgroundColor: '#48BB78', marginRight: 10 },
  rejectBtn: { backgroundColor: '#A0AEC0', marginLeft: 10 },
  buttonText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 }
});
