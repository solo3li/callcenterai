import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import WorkspaceScreen from './screens/WorkspaceScreen';

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <WorkspaceScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
});
